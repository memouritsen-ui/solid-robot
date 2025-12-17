import SwiftUI
import UniformTypeIdentifiers

/// Export format option
enum ExportFormat: String, CaseIterable, Identifiable {
    case markdown
    case json
    case pdf
    case docx
    case pptx
    case xlsx

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .markdown: return "Markdown (.md)"
        case .json: return "JSON (.json)"
        case .pdf: return "PDF (.pdf)"
        case .docx: return "Word (.docx)"
        case .pptx: return "PowerPoint (.pptx)"
        case .xlsx: return "Excel (.xlsx)"
        }
    }

    var icon: String {
        switch self {
        case .markdown: return "doc.text"
        case .json: return "curlybraces"
        case .pdf: return "doc.fill"
        case .docx: return "doc.richtext"
        case .pptx: return "rectangle.stack"
        case .xlsx: return "tablecells"
        }
    }

    var fileExtension: String {
        switch self {
        case .markdown: return "md"
        case .json: return "json"
        case .pdf: return "pdf"
        case .docx: return "docx"
        case .pptx: return "pptx"
        case .xlsx: return "xlsx"
        }
    }

    var contentType: UTType {
        switch self {
        case .markdown: return UTType.plainText
        case .json: return UTType.json
        case .pdf: return UTType.pdf
        case .docx: return UTType(filenameExtension: "docx") ?? .data
        case .pptx: return UTType(filenameExtension: "pptx") ?? .data
        case .xlsx: return UTType(filenameExtension: "xlsx") ?? .data
        }
    }
}

/// Export state for tracking export progress
enum ExportState: Equatable {
    case idle
    case exporting
    case success(URL)
    case failure(String)
}

/// View for exporting research results to various formats
struct ExportView: View {
    let sessionId: String
    @Environment(\.dismiss) private var dismiss

    @State private var selectedFormat: ExportFormat = .markdown
    @State private var exportState: ExportState = .idle
    @State private var includeMetadata: Bool = true
    @State private var includeSources: Bool = true

    private let baseURL = "http://localhost:8002"

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView

            Divider()

            // Content
            Form {
                formatSelectionSection
                optionsSection
                exportButtonSection
                statusSection
            }
            .formStyle(.grouped)
        }
        .frame(width: 400, height: 450)
    }

    // MARK: - Header

    private var headerView: some View {
        HStack {
            Text("Export Research")
                .font(.headline)
            Spacer()
            Button("Cancel") {
                dismiss()
            }
            .keyboardShortcut(.cancelAction)
        }
        .padding()
    }

    // MARK: - Format Selection

    private var formatSelectionSection: some View {
        Section("Export Format") {
            Picker("Format", selection: $selectedFormat) {
                ForEach(ExportFormat.allCases) { format in
                    Label(format.displayName, systemImage: format.icon)
                        .tag(format)
                }
            }
            .pickerStyle(.radioGroup)

            Text(formatDescription)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }

    private var formatDescription: String {
        switch selectedFormat {
        case .markdown:
            return "Plain text with formatting. Easy to read and edit."
        case .json:
            return "Structured data format. Best for programmatic use."
        case .pdf:
            return "Professional document. Best for sharing."
        case .docx:
            return "Microsoft Word format. Easy to edit in Word."
        case .pptx:
            return "PowerPoint presentation. Good for meetings."
        case .xlsx:
            return "Excel spreadsheet. Best for data analysis."
        }
    }

    // MARK: - Options

    private var optionsSection: some View {
        Section("Options") {
            Toggle("Include metadata", isOn: $includeMetadata)
            Toggle("Include source list", isOn: $includeSources)
        }
    }

    // MARK: - Export Button

    private var exportButtonSection: some View {
        Section {
            Button(action: exportReport) {
                HStack {
                    if case .exporting = exportState {
                        ProgressView()
                            .controlSize(.small)
                            .padding(.trailing, 4)
                    }
                    Text(exportButtonText)
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(isExportDisabled)
        }
    }

    private var exportButtonText: String {
        switch exportState {
        case .exporting:
            return "Exporting..."
        default:
            return "Export as \(selectedFormat.displayName)"
        }
    }

    private var isExportDisabled: Bool {
        if case .exporting = exportState {
            return true
        }
        return sessionId.isEmpty
    }

    // MARK: - Status

    @ViewBuilder
    private var statusSection: some View {
        switch exportState {
        case .idle:
            EmptyView()

        case .exporting:
            Section {
                HStack {
                    ProgressView()
                        .controlSize(.small)
                    Text("Preparing export...")
                        .foregroundColor(.secondary)
                }
            }

        case .success(let url):
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Label("Export successful!", systemImage: "checkmark.circle.fill")
                        .foregroundColor(.green)

                    Text("Saved to: \(url.lastPathComponent)")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    HStack {
                        Button("Open File") {
                            NSWorkspace.shared.open(url)
                        }

                        Button("Show in Finder") {
                            NSWorkspace.shared.selectFile(url.path, inFileViewerRootedAtPath: url.deletingLastPathComponent().path)
                        }
                    }
                }
            }

        case .failure(let message):
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Label("Export failed", systemImage: "xmark.circle.fill")
                        .foregroundColor(.red)

                    Text(message)
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Button("Try Again") {
                        exportState = .idle
                    }
                }
            }
        }
    }

    // MARK: - Export Logic

    private func exportReport() {
        guard !sessionId.isEmpty else { return }

        exportState = .exporting

        Task {
            do {
                let data = try await fetchExport()
                let savedURL = try await saveFile(data: data)
                exportState = .success(savedURL)
            } catch {
                exportState = .failure(error.localizedDescription)
            }
        }
    }

    private func fetchExport() async throws -> Data {
        guard let url = URL(string: "\(baseURL)/api/export") else {
            throw ExportError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "session_id": sessionId,
            "format": selectedFormat.rawValue,
            "options": [
                "include_metadata": includeMetadata,
                "include_sources": includeSources
            ]
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw ExportError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            // Try to parse error message
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let detail = json["detail"] as? String {
                throw ExportError.serverError(detail)
            }
            throw ExportError.httpError(httpResponse.statusCode)
        }

        return data
    }

    private func saveFile(data: Data) async throws -> URL {
        return try await MainActor.run {
            let savePanel = NSSavePanel()
            savePanel.title = "Save Research Report"
            savePanel.nameFieldStringValue = "research_report.\(selectedFormat.fileExtension)"
            savePanel.allowedContentTypes = [selectedFormat.contentType]
            savePanel.canCreateDirectories = true

            guard savePanel.runModal() == .OK, let url = savePanel.url else {
                throw ExportError.cancelled
            }

            try data.write(to: url)
            return url
        }
    }
}

// MARK: - Export Errors

enum ExportError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(Int)
    case serverError(String)
    case cancelled

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid export URL"
        case .invalidResponse:
            return "Invalid server response"
        case .httpError(let code):
            return "Server error (HTTP \(code))"
        case .serverError(let message):
            return message
        case .cancelled:
            return "Export was cancelled"
        }
    }
}

// MARK: - Preview

#if DEBUG
struct ExportView_Previews: PreviewProvider {
    static var previews: some View {
        ExportView(sessionId: "test-session-123")
    }
}
#endif
