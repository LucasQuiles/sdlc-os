/**
 * AST-based function extraction using the TypeScript compiler API.
 * Reads file paths from stdin (one per line), outputs JSON to stdout.
 *
 * For each function/arrow/method, emits:
 *   name, file, line, params, body_hash, line_count, branch_count, nesting_depth, exported
 *
 * Requires: typescript (resolved from project node_modules or globally)
 */

const fs = require('fs');
const crypto = require('crypto');
const readline = require('readline');
const path = require('path');

// Resolve TypeScript compiler — try project-local first, then global
let ts;
try {
  const projectRoot = process.cwd();
  const localTs = path.join(projectRoot, 'node_modules', 'typescript');
  ts = require(localTs);
} catch {
  try {
    ts = require('typescript');
  } catch {
    console.log(JSON.stringify({
      error: "typescript not found — install typescript in project or globally. Run: npm install -g typescript",
      functions: [],
      file_count: 0
    }));
    process.exit(0);
  }
}

const rl = readline.createInterface({ input: process.stdin });
const filePaths = [];

rl.on('line', (line) => {
  const trimmed = line.trim();
  if (trimmed) filePaths.push(trimmed);
});

rl.on('close', () => {
  const functions = [];

  for (const filePath of filePaths) {
    try {
      const sourceText = fs.readFileSync(filePath, 'utf8');
      const sourceFile = ts.createSourceFile(
        filePath,
        sourceText,
        ts.ScriptTarget.Latest,
        true, // setParentNodes
        filePath.endsWith('.tsx') || filePath.endsWith('.jsx')
          ? ts.ScriptKind.TSX
          : ts.ScriptKind.TS
      );

      visitNode(sourceFile, sourceFile, filePath, functions, sourceText);
    } catch {
      // Skip files that fail to parse
    }
  }

  console.log(JSON.stringify({ functions, file_count: filePaths.length }, null, 2));
});

function visitNode(node, sourceFile, filePath, functions, sourceText) {
  const info = extractFunctionInfo(node, sourceFile, filePath, sourceText);
  if (info) {
    functions.push(info);
  }

  ts.forEachChild(node, (child) => {
    visitNode(child, sourceFile, filePath, functions, sourceText);
  });
}

function extractFunctionInfo(node, sourceFile, filePath, sourceText) {
  let name = null;
  let bodyNode = null;
  let paramsNode = null;
  let isExported = false;

  // Function declarations: function foo() {}
  if (ts.isFunctionDeclaration(node) && node.name && node.body) {
    name = node.name.text;
    bodyNode = node.body;
    paramsNode = node.parameters;
    isExported = hasExportModifier(node);
  }
  // Variable declarations with arrow/function expressions: const foo = () => {}
  else if (
    ts.isVariableStatement(node) &&
    node.declarationList.declarations.length === 1
  ) {
    const decl = node.declarationList.declarations[0];
    if (
      ts.isIdentifier(decl.name) &&
      decl.initializer &&
      (ts.isArrowFunction(decl.initializer) || ts.isFunctionExpression(decl.initializer)) &&
      decl.initializer.body
    ) {
      name = decl.name.text;
      bodyNode = decl.initializer.body;
      paramsNode = decl.initializer.parameters;
      isExported = hasExportModifier(node);
    }
  }
  // Method declarations in classes/objects
  else if (ts.isMethodDeclaration(node) && node.name && node.body) {
    name = ts.isIdentifier(node.name) ? node.name.text : node.name.getText(sourceFile);
    bodyNode = node.body;
    paramsNode = node.parameters;
    isExported = false; // methods are accessed via their class
  }

  if (!name || !bodyNode) return null;

  // Extract body text and compute metrics
  const bodyStart = bodyNode.getStart(sourceFile);
  const bodyEnd = bodyNode.getEnd();
  const bodyText = sourceText.slice(bodyStart, bodyEnd);

  const startLine = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;
  const lineCount = bodyText.split('\n').length;

  // Normalize body for hash: collapse whitespace, remove string literals
  const normalized = bodyText
    .replace(/\/\/.*$/gm, '')       // strip line comments
    .replace(/\/\*[\s\S]*?\*\//g, '') // strip block comments
    .replace(/'[^']*'|"[^"]*"|`[^`]*`/g, '""') // normalize strings
    .replace(/\s+/g, ' ')
    .trim();
  const bodyHash = crypto.createHash('sha256').update(normalized).digest('hex').slice(0, 16);

  // Count branches via AST node kinds
  let branchCount = 0;
  let maxNesting = 0;
  countComplexity(bodyNode, 0);

  function countComplexity(n, depth) {
    if (
      ts.isIfStatement(n) ||
      ts.isSwitchStatement(n) ||
      ts.isConditionalExpression(n) ||
      ts.isCaseClause(n) ||
      (ts.isBinaryExpression(n) && (n.operatorToken.kind === ts.SyntaxKind.QuestionQuestionToken || n.operatorToken.kind === ts.SyntaxKind.BarBarToken || n.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken))
    ) {
      branchCount++;
    }
    const newDepth = ts.isBlock(n) ? depth + 1 : depth;
    if (newDepth > maxNesting) maxNesting = newDepth;
    ts.forEachChild(n, (child) => countComplexity(child, newDepth));
  }

  // Extract parameter signature
  const params = paramsNode
    ? paramsNode.map(p => p.getText(sourceFile)).join(', ')
    : '';

  return {
    name,
    file: filePath,
    line: startLine,
    params,
    body_hash: bodyHash,
    line_count: lineCount,
    branch_count: branchCount,
    nesting_depth: maxNesting,
    exported: isExported
  };
}

function hasExportModifier(node) {
  if (!node.modifiers) return false;
  return node.modifiers.some(m => m.kind === ts.SyntaxKind.ExportKeyword);
}
