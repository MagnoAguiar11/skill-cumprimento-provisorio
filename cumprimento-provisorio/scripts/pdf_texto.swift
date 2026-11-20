// PDF no macOS sem instalar nada (PDFKit).
//   swift pdf_texto.swift processo.pdf > processo.txt        texto, com marca de página
//   swift pdf_texto.swift processo.pdf --imagem 3,7 [pasta]  salva as páginas 3 e 7 em PNG (para páginas escaneadas)
import AppKit
import PDFKit

let args = CommandLine.arguments
guard args.count > 1, let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
    FileHandle.standardError.write("uso: swift pdf_texto.swift arquivo.pdf [--imagem 3,7 [pasta]]\n".data(using: .utf8)!); exit(1)
}
if args.count > 3 && args[2] == "--imagem" {
    let pasta = args.count > 4 ? args[4] : "."
    for n in args[3].split(separator: ",").compactMap({ Int($0) }) {
        guard let pagina = doc.page(at: n - 1) else { continue }
        let img = pagina.thumbnail(of: CGSize(width: 1600, height: 2200), for: .mediaBox)
        guard let tiff = img.tiffRepresentation, let png = NSBitmapImageRep(data: tiff)?.representation(using: .png, properties: [:]) else { continue }
        let destino = "\(pasta)/pagina-\(n).png"
        try? png.write(to: URL(fileURLWithPath: destino))
        print(destino)
    }
} else {
    for i in 0..<doc.pageCount { print("=== página \(i + 1) ===\n" + (doc.page(at: i)?.string ?? "")) }
}
