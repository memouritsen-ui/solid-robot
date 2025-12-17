import SwiftUI

/// Main research interface with query input, progress tracking, and live stats
struct ResearchView: View {
    @StateObject private var viewModel = ResearchViewModel()
    @State private var inputQuery: String = ""
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            // Main content
            ScrollView {
                VStack(spacing: 24) {
                    // Query input section
                    queryInputSection

                    // Progress section (only shown when researching or complete)
                    if viewModel.isResearching || viewModel.currentPhase == .complete {
                        progressSection
                    }
                }
                .padding()
            }

            Divider()

            // Error banner
            if let error = viewModel.errorMessage {
                errorBanner(error)
            }

            // Action buttons
            actionButtonsSection
        }
        .navigationTitle("Research")
        .toolbar {
            ToolbarItemGroup(placement: .automatic) {
                // Privacy mode indicator
                HStack(spacing: 4) {
                    Image(systemName: viewModel.privacyMode.icon)
                        .foregroundColor(viewModel.privacyMode == .localOnly ? .green : .blue)
                    Text(viewModel.privacyMode.displayName)
                        .font(.caption)
                }
            }
        }
        .sheet(isPresented: $viewModel.showingExport) {
            if let sessionId = viewModel.sessionId {
                ExportView(sessionId: sessionId)
            }
        }
    }

    // MARK: - Query Input Section

    private var queryInputSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Research Query")
                .font(.headline)

            HStack(alignment: .bottom, spacing: 12) {
                // Privacy mode picker
                PrivacyModePicker(selection: $viewModel.privacyMode)

                // Query input
                TextField("Enter your research question...", text: $inputQuery, axis: .vertical)
                    .textFieldStyle(.plain)
                    .lineLimit(1...5)
                    .focused($isInputFocused)
                    .disabled(viewModel.isResearching)
                    .onSubmit {
                        startResearch()
                    }
                    .padding(10)
                    .background(Color(.textBackgroundColor))
                    .cornerRadius(8)
            }

            Text("Ask a detailed question. The AI will search, verify, and synthesize findings.")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.controlBackgroundColor))
        .cornerRadius(12)
    }

    // MARK: - Progress Section

    private var progressSection: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Phase indicator
            phaseIndicator

            // Progress bar
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Overall Progress")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("\(Int(viewModel.progress * 100))%")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                ProgressView(value: viewModel.progress, total: 1.0)
                    .progressViewStyle(.linear)
            }

            // Live statistics
            statisticsGrid
        }
        .padding()
        .background(Color(.controlBackgroundColor))
        .cornerRadius(12)
    }

    // MARK: - Phase Indicator

    private var phaseIndicator: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Current Phase")
                .font(.subheadline)
                .foregroundColor(.secondary)

            // Phase steps (horizontal)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(ResearchPhase.allCases.filter { $0 != .idle && $0 != .complete }, id: \.self) { phase in
                        phaseStepView(phase: phase)
                    }
                }
            }
        }
    }

    private func phaseStepView(phase: ResearchPhase) -> some View {
        let isActive = viewModel.currentPhase == phase
        let isComplete = viewModel.currentPhase.stepNumber > phase.stepNumber

        return VStack(spacing: 4) {
            ZStack {
                Circle()
                    .fill(isActive ? Color.blue : (isComplete ? Color.green : Color.gray.opacity(0.3)))
                    .frame(width: 32, height: 32)

                Image(systemName: isComplete ? "checkmark" : phase.icon)
                    .font(.system(size: 14))
                    .foregroundColor(.white)
            }

            Text(phase.displayName)
                .font(.caption)
                .foregroundColor(isActive ? .primary : .secondary)
                .lineLimit(1)
        }
        .frame(minWidth: 70)
    }

    // MARK: - Statistics Grid

    private var statisticsGrid: some View {
        VStack(spacing: 12) {
            HStack(spacing: 12) {
                statCard(
                    title: "Entities",
                    value: "\(viewModel.entitiesCount)",
                    icon: "tag.fill",
                    color: .blue
                )

                statCard(
                    title: "Facts",
                    value: "\(viewModel.factsCount)",
                    icon: "doc.text.fill",
                    color: .green
                )
            }

            HStack(spacing: 12) {
                statCard(
                    title: "Sources",
                    value: "\(viewModel.sourcesCount)",
                    icon: "link",
                    color: .orange
                )

                statCard(
                    title: "Saturation",
                    value: String(format: "%.0f%%", viewModel.saturationPercent),
                    icon: "chart.bar.fill",
                    color: .purple
                )
            }
        }
    }

    private func statCard(title: String, value: String, icon: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.caption)
                Text(title)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Text(value)
                .font(.title2)
                .fontWeight(.semibold)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color(.textBackgroundColor))
        .cornerRadius(8)
    }

    // MARK: - Error Banner

    private func errorBanner(_ error: String) -> some View {
        HStack {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.orange)
            Text(error)
                .font(.caption)
                .foregroundColor(.secondary)
            Spacer()
            Button("Dismiss") {
                viewModel.errorMessage = nil
            }
            .font(.caption)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(Color.orange.opacity(0.1))
    }

    // MARK: - Action Buttons Section

    private var actionButtonsSection: some View {
        HStack(spacing: 12) {
            // Reset button (only shown when complete or error)
            if viewModel.currentPhase == .complete || viewModel.errorMessage != nil {
                Button(action: {
                    viewModel.reset()
                    inputQuery = ""
                }) {
                    HStack {
                        Image(systemName: "arrow.counterclockwise")
                        Text("New Research")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }

            // Export button (only shown when complete)
            if viewModel.currentPhase == .complete {
                Button(action: {
                    viewModel.showingExport = true
                }) {
                    HStack {
                        Image(systemName: "square.and.arrow.up")
                        Text("Export Report")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }

            // Start/Stop button
            if viewModel.isResearching {
                Button(action: {
                    Task {
                        await viewModel.stopResearch()
                    }
                }) {
                    HStack {
                        Image(systemName: "stop.fill")
                        Text("Stop Research")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .tint(.red)
            } else if viewModel.currentPhase != .complete {
                Button(action: startResearch) {
                    HStack {
                        Image(systemName: "play.fill")
                        Text("Start Research")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(inputQuery.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
        .padding()
    }

    // MARK: - Private Methods

    private func startResearch() {
        let query = inputQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !query.isEmpty else { return }

        viewModel.query = query

        Task {
            await viewModel.startResearch(query: query)
        }
    }
}

// Preview requires Xcode, not available in Swift Package Manager
// #Preview { ResearchView() }
