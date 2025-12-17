import SwiftUI

/// Detailed view of a single research session from the library
struct SessionDetailView: View {
    let session: LibrarySessionDetail

    @State private var selectedTab: DetailTab = .summary
    @State private var showingExport = false

    enum DetailTab: String, CaseIterable {
        case summary = "Summary"
        case facts = "Facts"
        case sources = "Sources"
        case entities = "Entities"

        var icon: String {
            switch self {
            case .summary: return "doc.text"
            case .facts: return "checkmark.circle"
            case .sources: return "link"
            case .entities: return "tag"
            }
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header with query and metadata
            headerSection

            Divider()

            // Tab picker
            tabPicker

            Divider()

            // Tab content
            tabContent
        }
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button {
                    showingExport = true
                } label: {
                    Label("Export", systemImage: "square.and.arrow.up")
                }
            }
        }
        .sheet(isPresented: $showingExport) {
            ExportView(report: sessionToReport())
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Query
            Text(session.query)
                .font(.title2)
                .fontWeight(.semibold)
                .lineLimit(3)

            // Metadata row
            HStack(spacing: 16) {
                // Domain badge
                HStack(spacing: 4) {
                    Image(systemName: "globe")
                    Text(session.domain)
                }
                .font(.caption)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.blue.opacity(0.2))
                .foregroundColor(.blue)
                .cornerRadius(6)

                // Privacy mode
                HStack(spacing: 4) {
                    Image(systemName: session.privacyMode == "local_only" ? "lock.fill" : "cloud")
                    Text(session.privacyMode == "local_only" ? "Local Only" : "Cloud")
                }
                .font(.caption)
                .foregroundColor(.secondary)

                // Status
                HStack(spacing: 4) {
                    Circle()
                        .fill(session.status == "completed" ? Color.green : Color.orange)
                        .frame(width: 8, height: 8)
                    Text(session.status.capitalized)
                }
                .font(.caption)
                .foregroundColor(.secondary)

                Spacer()

                // Confidence score
                if let confidence = session.confidenceScore {
                    HStack(spacing: 4) {
                        Image(systemName: "chart.bar.fill")
                        Text(String(format: "%.0f%% confidence", confidence * 100))
                    }
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(confidenceColor(confidence).opacity(0.2))
                    .foregroundColor(confidenceColor(confidence))
                    .cornerRadius(6)
                }
            }

            // Stats row
            HStack(spacing: 20) {
                statBadge(count: session.facts.count, label: "Facts", icon: "doc.text.fill")
                statBadge(count: session.sources.count, label: "Sources", icon: "link")
                statBadge(count: session.entities.count, label: "Entities", icon: "tag.fill")
            }
        }
        .padding()
        .background(Color(.controlBackgroundColor))
    }

    private func statBadge(count: Int, label: String, icon: String) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .foregroundColor(.secondary)
            Text("\(count)")
                .fontWeight(.medium)
            Text(label)
                .foregroundColor(.secondary)
        }
        .font(.subheadline)
    }

    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.8 { return .green }
        if confidence >= 0.6 { return .orange }
        return .red
    }

    // MARK: - Tab Picker

    private var tabPicker: some View {
        HStack(spacing: 0) {
            ForEach(DetailTab.allCases, id: \.self) { tab in
                Button {
                    selectedTab = tab
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: tab.icon)
                        Text(tab.rawValue)
                    }
                    .font(.subheadline)
                    .padding(.vertical, 8)
                    .padding(.horizontal, 16)
                    .background(selectedTab == tab ? Color.accentColor.opacity(0.2) : Color.clear)
                    .foregroundColor(selectedTab == tab ? .accentColor : .secondary)
                }
                .buttonStyle(.plain)
            }
            Spacer()
        }
        .padding(.horizontal)
    }

    // MARK: - Tab Content

    @ViewBuilder
    private var tabContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                switch selectedTab {
                case .summary:
                    summaryContent
                case .facts:
                    factsContent
                case .sources:
                    sourcesContent
                case .entities:
                    entitiesContent
                }
            }
            .padding()
        }
    }

    // MARK: - Summary Content

    private var summaryContent: some View {
        VStack(alignment: .leading, spacing: 16) {
            if let summary = session.summary, !summary.isEmpty {
                Text("Summary")
                    .font(.headline)

                Text(summary)
                    .font(.body)
                    .textSelection(.enabled)
            } else {
                Text("No summary available")
                    .foregroundColor(.secondary)
                    .italic()
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Facts Content

    private var factsContent: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Extracted Facts (\(session.facts.count))")
                .font(.headline)

            if session.facts.isEmpty {
                Text("No facts extracted")
                    .foregroundColor(.secondary)
                    .italic()
            } else {
                ForEach(Array(session.facts.enumerated()), id: \.offset) { index, fact in
                    factRow(fact, index: index + 1)
                }
            }
        }
    }

    private func factRow(_ fact: [String: AnyCodableValue], index: Int) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .top) {
                Text("\(index).")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(width: 24, alignment: .trailing)

                VStack(alignment: .leading, spacing: 4) {
                    if let claim = fact["claim"]?.stringValue {
                        Text(claim)
                            .font(.body)
                            .textSelection(.enabled)
                    }

                    HStack(spacing: 12) {
                        if let confidence = fact["confidence"]?.doubleValue {
                            Label(
                                String(format: "%.0f%%", confidence * 100),
                                systemImage: "chart.bar.fill"
                            )
                            .font(.caption)
                            .foregroundColor(.secondary)
                        }

                        if let source = fact["source"]?.stringValue {
                            Label(source, systemImage: "link")
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .lineLimit(1)
                        }
                    }
                }
            }
        }
        .padding(12)
        .background(Color(.textBackgroundColor))
        .cornerRadius(8)
    }

    // MARK: - Sources Content

    private var sourcesContent: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Sources (\(session.sources.count))")
                .font(.headline)

            if session.sources.isEmpty {
                Text("No sources available")
                    .foregroundColor(.secondary)
                    .italic()
            } else {
                ForEach(Array(session.sources.enumerated()), id: \.offset) { index, source in
                    sourceRow(source, index: index + 1)
                }
            }
        }
    }

    private func sourceRow(_ source: [String: AnyCodableValue], index: Int) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .top) {
                Text("\(index).")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(width: 24, alignment: .trailing)

                VStack(alignment: .leading, spacing: 4) {
                    if let title = source["title"]?.stringValue {
                        Text(title)
                            .font(.headline)
                            .lineLimit(2)
                    }

                    if let url = source["url"]?.stringValue {
                        Link(url, destination: URL(string: url) ?? URL(string: "about:blank")!)
                            .font(.caption)
                            .lineLimit(1)
                    }

                    HStack(spacing: 12) {
                        if let quality = source["quality_score"]?.doubleValue {
                            Label(
                                String(format: "Quality: %.0f%%", quality * 100),
                                systemImage: "star.fill"
                            )
                            .font(.caption)
                            .foregroundColor(.secondary)
                        }

                        if let provider = source["provider"]?.stringValue {
                            Label(provider, systemImage: "server.rack")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
        }
        .padding(12)
        .background(Color(.textBackgroundColor))
        .cornerRadius(8)
    }

    // MARK: - Entities Content

    private var entitiesContent: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Discovered Entities (\(session.entities.count))")
                .font(.headline)

            if session.entities.isEmpty {
                Text("No entities discovered")
                    .foregroundColor(.secondary)
                    .italic()
            } else {
                FlowLayout(spacing: 8) {
                    ForEach(session.entities, id: \.self) { entity in
                        Text(entity)
                            .font(.subheadline)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .cornerRadius(16)
                    }
                }
            }
        }
    }

    // MARK: - Helper Methods

    /// Convert session to report for export
    private func sessionToReport() -> ResearchReportResponse {
        ResearchReportResponse(
            sessionId: session.sessionId,
            query: session.query,
            domain: session.domain,
            summary: session.summary,
            facts: session.facts,
            sources: session.sources,
            entities: session.entities,
            confidenceScore: session.confidenceScore,
            limitations: nil,
            generatedAt: session.completedAt
        )
    }
}

// MARK: - Flow Layout for Entity Tags

struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = computeLayout(proposal: proposal, subviews: subviews)
        return result.size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = computeLayout(proposal: proposal, subviews: subviews)

        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(
                x: bounds.minX + result.positions[index].x,
                y: bounds.minY + result.positions[index].y
            ), proposal: .unspecified)
        }
    }

    private func computeLayout(proposal: ProposedViewSize, subviews: Subviews) -> (size: CGSize, positions: [CGPoint]) {
        var positions: [CGPoint] = []
        var currentX: CGFloat = 0
        var currentY: CGFloat = 0
        var lineHeight: CGFloat = 0
        var maxWidth: CGFloat = 0

        let maxX = proposal.width ?? .infinity

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)

            if currentX + size.width > maxX && currentX > 0 {
                currentX = 0
                currentY += lineHeight + spacing
                lineHeight = 0
            }

            positions.append(CGPoint(x: currentX, y: currentY))
            currentX += size.width + spacing
            lineHeight = max(lineHeight, size.height)
            maxWidth = max(maxWidth, currentX)
        }

        return (
            size: CGSize(width: maxWidth, height: currentY + lineHeight),
            positions: positions
        )
    }
}

// MARK: - Preview

#if DEBUG
struct SessionDetailView_Previews: PreviewProvider {
    static var previews: some View {
        SessionDetailView(session: LibrarySessionDetail(
            sessionId: "test-123",
            query: "What are the latest advances in quantum computing?",
            domain: "academic",
            privacyMode: "cloud_allowed",
            status: "completed",
            summary: "Quantum computing has seen significant advances in 2024...",
            facts: [
                ["claim": AnyCodableValue.string("IBM has a 1000+ qubit processor"), "confidence": AnyCodableValue.double(0.95)],
                ["claim": AnyCodableValue.string("Google achieved quantum supremacy"), "confidence": AnyCodableValue.double(0.88)]
            ],
            sources: [
                ["title": AnyCodableValue.string("IBM Quantum Roadmap"), "url": AnyCodableValue.string("https://ibm.com/quantum")]
            ],
            entities: ["quantum computing", "IBM", "Google", "qubit", "quantum supremacy"],
            confidenceScore: 0.85,
            startedAt: "2024-12-17T10:00:00Z",
            completedAt: "2024-12-17T10:15:00Z",
            saturationMetrics: nil
        ))
    }
}
#endif
