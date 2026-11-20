// Lê o texto de uma imagem com o Vision do macOS e imprime uma linha JSON por trecho:
// {"texto": "...", "x": .., "y": .., "w": .., "h": ..}  (pixels, origem no canto superior esquerdo)
//   swift ocr_linhas.swift print.png
import AppKit
import Foundation
import Vision

guard CommandLine.arguments.count > 1,
      let img = NSImage(contentsOfFile: CommandLine.arguments[1]),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write("uso: swift ocr_linhas.swift imagem.png\n".data(using: .utf8)!)
    exit(1)
}
let W = Double(cg.width), H = Double(cg.height)
let pedido = VNRecognizeTextRequest()
pedido.recognitionLevel = .accurate
pedido.recognitionLanguages = ["pt-BR"]
pedido.usesLanguageCorrection = false
try VNImageRequestHandler(cgImage: cg).perform([pedido])
for o in pedido.results ?? [] {
    guard let t = o.topCandidates(1).first?.string else { continue }
    let b = o.boundingBox
    let linha: [String: Any] = ["texto": t, "x": Int(b.minX * W), "y": Int((1 - b.maxY) * H),
                                "w": Int(b.width * W), "h": Int(b.height * H)]
    let dados = try JSONSerialization.data(withJSONObject: linha)
    print(String(data: dados, encoding: .utf8)!)
}
