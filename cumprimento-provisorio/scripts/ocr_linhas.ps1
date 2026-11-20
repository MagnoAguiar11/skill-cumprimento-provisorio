# Lê o texto de uma imagem com o OCR que já vem no Windows 10/11 (Windows.Media.Ocr), sem instalar nada.
# Imprime primeiro {"largura": .., "altura": ..} e depois uma linha JSON por linha de texto:
# {"texto": "...", "x": .., "y": .., "w": .., "h": ..}  (pixels, origem no canto superior esquerdo)
#   powershell -NoProfile -ExecutionPolicy Bypass -File ocr_linhas.ps1 C:\caminho\print.png
param([Parameter(Mandatory = $true)][string]$Imagem)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq "AsTask" -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq "IAsyncOperation``1" })[0]
function Esperar($operacao, [Type]$tipo) {
    $tarefa = $asTask.MakeGenericMethod($tipo).Invoke($null, @($operacao))
    $null = $tarefa.Wait(-1)
    $tarefa.Result
}

$arquivo = Esperar ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path $Imagem).ProviderPath)) ([Windows.Storage.StorageFile])
$fluxo = Esperar ($arquivo.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decodificador = Esperar ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($fluxo)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Esperar ($decodificador.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $motor) { throw "O Windows não tem nenhum idioma com OCR instalado." }
$resultado = Esperar ($motor.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])

@{ largura = $decodificador.PixelWidth; altura = $decodificador.PixelHeight } | ConvertTo-Json -Compress
foreach ($linha in $resultado.Lines) {
    $caixas = $linha.Words | ForEach-Object { $_.BoundingRect }
    $x = ($caixas | Measure-Object -Property X -Minimum).Minimum
    $y = ($caixas | Measure-Object -Property Y -Minimum).Minimum
    $x2 = ($caixas | ForEach-Object { $_.X + $_.Width } | Measure-Object -Maximum).Maximum
    $y2 = ($caixas | ForEach-Object { $_.Y + $_.Height } | Measure-Object -Maximum).Maximum
    @{ texto = $linha.Text; x = [int]$x; y = [int]$y; w = [int]($x2 - $x); h = [int]($y2 - $y) } | ConvertTo-Json -Compress
}
