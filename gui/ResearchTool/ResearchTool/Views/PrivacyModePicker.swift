import SwiftUI

/// Compact privacy mode selector for chat input area
struct PrivacyModePicker: View {
    @Binding var selection: PrivacyMode
    @State private var isExpanded: Bool = false

    var body: some View {
        Menu {
            ForEach(PrivacyMode.allCases) { mode in
                Button(action: {
                    selection = mode
                }) {
                    Label {
                        VStack(alignment: .leading) {
                            Text(mode.displayName)
                            Text(mode.description)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    } icon: {
                        Image(systemName: mode.icon)
                    }
                }
            }
        } label: {
            HStack(spacing: 4) {
                Image(systemName: selection.icon)
                    .foregroundColor(selection == .localOnly ? .green : .blue)
            }
            .padding(8)
            .background(Color(.controlBackgroundColor))
            .cornerRadius(8)
        }
        .menuStyle(.borderlessButton)
        .help(selection.description)
    }
}

// Preview requires Xcode, not available in Swift Package Manager
// #Preview { ... }
