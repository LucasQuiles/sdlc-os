#!/usr/bin/env node
// ABOUTME: Extracts function definitions from TS/JS using ts-morph AST analysis

import { Project, SyntaxKind } from 'ts-morph';
import { createHash } from 'crypto';
import { writeFileSync } from 'fs';
import { resolve, relative, extname } from 'path';

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const args = argv.slice(2);
  const opts = {
    sourceDir: null,
    output: null,
    types: '*.ts,*.tsx,*.js,*.jsx',
    includeTests: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--output' || arg === '-o') {
      opts.output = args[++i];
    } else if (arg === '--types' || arg === '-t') {
      opts.types = args[++i];
    } else if (arg === '--include-tests') {
      opts.includeTests = true;
    } else if (arg === '--help' || arg === '-h') {
      printUsage();
      process.exit(0);
    } else if (!arg.startsWith('-')) {
      opts.sourceDir = arg;
    } else {
      console.error(`Unknown option: ${arg}`);
      printUsage();
      process.exit(1);
    }
  }

  if (!opts.sourceDir) {
    console.error('Error: source directory is required.');
    printUsage();
    process.exit(1);
  }

  return opts;
}

function printUsage() {
  console.error(`
Usage: extract-functions-ast-ts.mjs <source-dir> [options]

Options:
  --output, -o FILE    Write JSON output to FILE (default: stdout)
  --types, -t GLOB     Comma-separated file globs (default: *.ts,*.tsx,*.js,*.jsx)
  --include-tests      Include test files (*.test.*, *.spec.*, __tests__/**, test/**)
  --help, -h           Show this help message
`);
}

// ---------------------------------------------------------------------------
// Test file detection
// ---------------------------------------------------------------------------

const TEST_PATTERNS = [
  /\.test\./,
  /\.spec\./,
  /[/\\]__tests__[/\\]/,
  /[/\\]test[/\\]/,
];

function isTestFile(filePath) {
  return TEST_PATTERNS.some((pat) => pat.test(filePath));
}

// ---------------------------------------------------------------------------
// Cyclomatic complexity calculation
// ---------------------------------------------------------------------------

/** Count branching constructs in a function body for cyclomatic complexity. */
function computeCyclomaticComplexity(node) {
  let complexity = 1; // base path

  node.forEachDescendant((child) => {
    switch (child.getKind()) {
      case SyntaxKind.IfStatement:
      case SyntaxKind.ForStatement:
      case SyntaxKind.ForInStatement:
      case SyntaxKind.ForOfStatement:
      case SyntaxKind.WhileStatement:
      case SyntaxKind.DoStatement:
      case SyntaxKind.CaseClause:
      case SyntaxKind.CatchClause:
      case SyntaxKind.ConditionalExpression:
        complexity++;
        break;
      case SyntaxKind.BinaryExpression: {
        const opKind = child.getOperatorToken().getKind();
        if (
          opKind === SyntaxKind.AmpersandAmpersandToken ||
          opKind === SyntaxKind.BarBarToken ||
          opKind === SyntaxKind.QuestionQuestionToken
        ) {
          complexity++;
        }
        break;
      }
      default:
        break;
    }
  });

  return complexity;
}

// ---------------------------------------------------------------------------
// AST fingerprinting — normalized SHA-256
// ---------------------------------------------------------------------------

/**
 * Walk the AST of a function node and produce a normalized string representation.
 * All identifiers are replaced with positional placeholders (_ID_0, _ID_1, ...),
 * ensuring structurally identical functions produce the same fingerprint regardless
 * of naming.
 */
function computeAstFingerprint(node) {
  const identifierMap = new Map();
  let idCounter = 0;
  const tokens = [];

  function walk(n) {
    const kind = n.getKind();
    const kindName = SyntaxKind[kind];

    if (kind === SyntaxKind.Identifier) {
      const text = n.getText();
      if (!identifierMap.has(text)) {
        identifierMap.set(text, `_ID_${idCounter++}`);
      }
      tokens.push(`Identifier:${identifierMap.get(text)}`);
    } else {
      tokens.push(kindName);
    }

    n.forEachChild(walk);
  }

  walk(node);

  const normalized = tokens.join('|');
  return createHash('sha256').update(normalized).digest('hex');
}

// ---------------------------------------------------------------------------
// Token sequence — DFS syntax kind names
// ---------------------------------------------------------------------------

function computeTokenSequence(node) {
  const kinds = [];

  function walk(n) {
    kinds.push(SyntaxKind[n.getKind()]);
    n.forEachChild(walk);
  }

  walk(node);
  return kinds;
}

// ---------------------------------------------------------------------------
// Decorator extraction
// ---------------------------------------------------------------------------

function getDecorators(node) {
  if (typeof node.getDecorators !== 'function') return [];
  return node.getDecorators().map((d) => {
    const name = d.getName?.();
    if (name) return name;
    // Fallback: extract from text
    const text = d.getText();
    const match = text.match(/@(\w+)/);
    return match ? match[1] : text;
  });
}

// ---------------------------------------------------------------------------
// JSDoc extraction — first line only
// ---------------------------------------------------------------------------

function getDocstring(node) {
  if (typeof node.getJsDocs !== 'function') return null;
  const docs = node.getJsDocs();
  if (docs.length === 0) return null;

  const comment = docs[0].getComment();
  if (!comment) return null;

  // comment can be a string or an array of JSDocText/JSDocLink nodes
  const text = typeof comment === 'string'
    ? comment
    : Array.isArray(comment)
      ? comment.map((c) => (typeof c === 'string' ? c : c.getText?.() ?? '')).join('')
      : String(comment);

  const firstLine = text.split('\n')[0].trim();
  return firstLine || null;
}

// ---------------------------------------------------------------------------
// Parameter extraction
// ---------------------------------------------------------------------------

function extractParams(node) {
  if (typeof node.getParameters !== 'function') return [];
  return node.getParameters().map((p) => {
    const typeNode = p.getTypeNode();
    return {
      name: p.getName(),
      type: typeNode ? typeNode.getText() : (p.getType()?.getText() ?? null),
      default: p.getInitializer()?.getText() ?? null,
      optional: p.isOptional(),
    };
  });
}

// ---------------------------------------------------------------------------
// Return type extraction
// ---------------------------------------------------------------------------

function getReturnType(node) {
  // Prefer explicit annotation
  if (typeof node.getReturnTypeNode === 'function') {
    const rtNode = node.getReturnTypeNode();
    if (rtNode) return rtNode.getText();
  }
  // Fallback to inferred type (may be verbose)
  if (typeof node.getReturnType === 'function') {
    try {
      const rt = node.getReturnType();
      const text = rt.getText(node);
      // Avoid excessively long inferred types
      if (text && text.length < 200) return text;
    } catch {
      // ignore inference failures
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Signature extraction
// ---------------------------------------------------------------------------

function getSignature(node, name) {
  // For arrow functions / function expressions, build from parts
  const params = typeof node.getParameters === 'function'
    ? node.getParameters().map((p) => p.getText()).join(', ')
    : '';

  const typeParams = typeof node.getTypeParameters === 'function'
    ? node.getTypeParameters()
    : [];
  const generics = typeParams.length > 0
    ? `<${typeParams.map((tp) => tp.getText()).join(', ')}>`
    : '';

  const retType = getReturnType(node);
  const retPart = retType ? `: ${retType}` : '';

  const kind = node.getKind();
  if (kind === SyntaxKind.Constructor) {
    return `constructor(${params})`;
  }
  if (kind === SyntaxKind.GetAccessor) {
    return `get ${name}()${retPart}`;
  }
  if (kind === SyntaxKind.SetAccessor) {
    return `set ${name}(${params})`;
  }

  return `${name}${generics}(${params})${retPart}`;
}

// ---------------------------------------------------------------------------
// Export type detection
// ---------------------------------------------------------------------------

function getExportType(node) {
  const kind = node.getKind();

  // Methods, getters, setters, constructors are "method"
  if (
    kind === SyntaxKind.MethodDeclaration ||
    kind === SyntaxKind.GetAccessor ||
    kind === SyntaxKind.SetAccessor ||
    kind === SyntaxKind.Constructor
  ) {
    return 'method';
  }

  // Check direct export modifiers
  if (typeof node.isExported === 'function' && node.isExported()) {
    if (typeof node.isDefaultExport === 'function' && node.isDefaultExport()) {
      return 'default';
    }
    return 'named';
  }

  // For variable declarations containing arrow/function expressions,
  // check the parent VariableStatement
  if (kind === SyntaxKind.ArrowFunction || kind === SyntaxKind.FunctionExpression) {
    const varDecl = node.getFirstAncestorByKind(SyntaxKind.VariableDeclaration);
    if (varDecl) {
      const varStmt = varDecl.getFirstAncestorByKind(SyntaxKind.VariableStatement);
      if (varStmt) {
        if (typeof varStmt.isExported === 'function' && varStmt.isExported()) {
          if (typeof varStmt.isDefaultExport === 'function' && varStmt.isDefaultExport()) {
            return 'default';
          }
          return 'named';
        }
      }
    }
  }

  return 'internal';
}

// ---------------------------------------------------------------------------
// Body line count
// ---------------------------------------------------------------------------

function getBodyLines(node) {
  const body = typeof node.getBody === 'function' ? node.getBody() : null;
  if (!body) return 0;
  const startLine = body.getStartLineNumber();
  const endLine = body.getEndLineNumber();
  return Math.max(0, endLine - startLine + 1);
}

// ---------------------------------------------------------------------------
// Language detection from file extension
// ---------------------------------------------------------------------------

function detectLanguage(filePath) {
  const ext = extname(filePath).toLowerCase();
  if (ext === '.ts' || ext === '.tsx') return 'typescript';
  return 'javascript';
}

// ---------------------------------------------------------------------------
// Core: extract functions from a single source file
// ---------------------------------------------------------------------------

function extractFunctionsFromFile(sourceFile, baseDir) {
  const filePath = relative(baseDir, sourceFile.getFilePath());
  const language = detectLanguage(filePath);
  const results = [];

  /**
   * Build the standard record for any function-like node.
   */
  function buildRecord(node, name, qualifiedName, exportTypeOverride) {
    const line = node.getStartLineNumber();
    const endLine = node.getEndLineNumber();

    return {
      file: filePath,
      name,
      qualified_name: qualifiedName,
      line,
      end_line: endLine,
      signature: getSignature(node, name),
      params: extractParams(node),
      return_type: getReturnType(node),
      decorators: getDecorators(node),
      docstring: getDocstring(node),
      body_lines: getBodyLines(node),
      cyclomatic_complexity: computeCyclomaticComplexity(node),
      ast_fingerprint: computeAstFingerprint(node),
      token_sequence: computeTokenSequence(node),
      export_type: exportTypeOverride ?? getExportType(node),
      language,
    };
  }

  // --- Function declarations ---
  for (const fn of sourceFile.getFunctions()) {
    const name = fn.getName() || '(anonymous)';
    results.push(buildRecord(fn, name, name));
  }

  // --- Arrow functions and function expressions assigned to variables ---
  for (const varStmt of sourceFile.getVariableStatements()) {
    for (const decl of varStmt.getDeclarationList().getDeclarations()) {
      const init = decl.getInitializer();
      if (!init) continue;
      const kind = init.getKind();
      if (kind === SyntaxKind.ArrowFunction || kind === SyntaxKind.FunctionExpression) {
        const name = decl.getName();
        results.push(buildRecord(init, name, name));
      }
    }
  }

  // --- Classes: methods, getters, setters, constructors ---
  for (const cls of sourceFile.getClasses()) {
    const className = cls.getName() || '(anonymous)';

    // Constructor
    for (const ctor of cls.getConstructors()) {
      const qName = `${className}.constructor`;
      results.push(buildRecord(ctor, 'constructor', qName, 'method'));
    }

    // Methods
    for (const method of cls.getMethods()) {
      const methodName = method.getName();
      const qName = `${className}.${methodName}`;
      results.push(buildRecord(method, methodName, qName, 'method'));
    }

    // Getters
    for (const getter of cls.getGetAccessors()) {
      const name = getter.getName();
      const qName = `${className}.${name}`;
      results.push(buildRecord(getter, name, qName, 'method'));
    }

    // Setters
    for (const setter of cls.getSetAccessors()) {
      const name = setter.getName();
      const qName = `${className}.${name}`;
      results.push(buildRecord(setter, name, qName, 'method'));
    }
  }

  // --- Object literal method shorthand (top-level variable assignments) ---
  for (const varStmt of sourceFile.getVariableStatements()) {
    for (const decl of varStmt.getDeclarationList().getDeclarations()) {
      const init = decl.getInitializer();
      if (!init || init.getKind() !== SyntaxKind.ObjectLiteralExpression) continue;

      const objName = decl.getName();
      for (const prop of init.getProperties()) {
        const kind = prop.getKind();

        // Method shorthand: { foo() { ... } }
        if (kind === SyntaxKind.MethodDeclaration) {
          const name = prop.getName();
          const qName = `${objName}.${name}`;
          results.push(buildRecord(prop, name, qName, 'method'));
        }

        // Property assignment with arrow/function: { foo: () => { ... } }
        if (kind === SyntaxKind.PropertyAssignment) {
          const propInit = prop.getInitializer?.();
          if (propInit) {
            const propInitKind = propInit.getKind();
            if (propInitKind === SyntaxKind.ArrowFunction || propInitKind === SyntaxKind.FunctionExpression) {
              const name = prop.getName();
              const qName = `${objName}.${name}`;
              results.push(buildRecord(propInit, name, qName, 'method'));
            }
          }
        }
      }
    }
  }

  return results;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  const opts = parseArgs(process.argv);
  const sourceDir = resolve(opts.sourceDir);

  // Build glob patterns from --types
  const typeGlobs = opts.types.split(',').map((g) => g.trim());
  const fileGlobs = typeGlobs.map((g) => `${sourceDir}/**/${g}`);

  // Create ts-morph project (no tsconfig required — we add files by glob)
  const project = new Project({
    compilerOptions: {
      allowJs: true,
      checkJs: false,
      noEmit: true,
      skipLibCheck: true,
      // Accept all TS features
      target: 99, // ESNext
      module: 99, // ESNext
      moduleResolution: 100, // Bundler
      jsx: 4, // ReactJSX
      esModuleInterop: true,
      strict: false,
    },
    skipAddingFilesFromTsConfig: true,
  });

  // Add source files matching the globs
  for (const glob of fileGlobs) {
    project.addSourceFilesAtPaths(glob);
  }

  const allFunctions = [];

  for (const sourceFile of project.getSourceFiles()) {
    const filePath = sourceFile.getFilePath();

    // Filter test files unless --include-tests
    if (!opts.includeTests && isTestFile(filePath)) {
      continue;
    }

    try {
      const functions = extractFunctionsFromFile(sourceFile, sourceDir);
      allFunctions.push(...functions);
    } catch (err) {
      console.error(`[WARN] Skipping ${filePath}: ${err.message}`);
    }
  }

  // Output
  const json = JSON.stringify(allFunctions, null, 2);

  if (opts.output) {
    writeFileSync(resolve(opts.output), json, 'utf-8');
    console.error(`Wrote ${allFunctions.length} functions to ${opts.output}`);
  } else {
    process.stdout.write(json + '\n');
  }
}

main();
