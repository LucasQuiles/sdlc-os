import Foundation
import CryptoKit
import SwiftParser
import SwiftSyntax

func sha256(_ bytes: Data) -> String {
    SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined()
}

func inspect(_ path: String) throws -> [String: Any] {
    let source = try String(contentsOfFile: path, encoding: .utf8)
    let tree = Parser.parse(source: source)
    guard !tree.hasError, tree.description == source else {
        throw NSError(domain: "Invalid Swift syntax", code: 1, userInfo: [NSLocalizedDescriptionKey: path])
    }
    let converter = SourceLocationConverter(fileName: path, tree: tree)
    var count = 0
    var functions: [[String: Any]] = []
    func walk(_ node: Syntax) throws {
        count += 1
        var signature: String?
        if let function = node.as(FunctionDeclSyntax.self) {
            signature = function.name.text + function.signature.trimmedDescription
        } else if let initializer = node.as(InitializerDeclSyntax.self) {
            signature = "init" + initializer.signature.trimmedDescription
        } else if node.is(DeinitializerDeclSyntax.self) {
            signature = "deinit"
        } else if let accessor = node.as(AccessorDeclSyntax.self) {
            signature = accessor.accessorSpecifier.text
        } else if let binding = node.as(PatternBindingSyntax.self), binding.accessorBlock != nil {
            signature = binding.pattern.trimmedDescription
        } else if let subscriptDecl = node.as(SubscriptDeclSyntax.self) {
            signature = "subscript" + subscriptDecl.parameterClause.trimmedDescription
        }
        if let signature {
            let lexical = node.tokens(viewMode: .all).map { [String(describing: $0.tokenKind), $0.text] }
            let syntax = try JSONSerialization.data(withJSONObject: lexical)
            functions.append([
                "name": signature, "signature": signature,
                "line": converter.location(for: node.positionAfterSkippingLeadingTrivia).line,
                "end_line": converter.location(for: node.endPositionBeforeTrailingTrivia).line,
                "start_utf8": node.positionAfterSkippingLeadingTrivia.utf8Offset,
                "end_utf8": node.endPositionBeforeTrailingTrivia.utf8Offset,
                "syntax_sha256": sha256(syntax),
                "source_sha256": sha256(Data(node.trimmedDescription.utf8))
            ])
        }
        for child in node.children(viewMode: .all) { try walk(child) }
    }
    try walk(Syntax(tree))
    return ["nodes": count, "functions": functions]
}

do {
    var result: [String: Any] = [:]
    for path in CommandLine.arguments.dropFirst() { result[path] = try inspect(path) }
    let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
    FileHandle.standardOutput.write(data)
} catch {
    FileHandle.standardError.write(Data("Swift syntax analysis failed: \(error)\n".utf8))
    exit(1)
}
