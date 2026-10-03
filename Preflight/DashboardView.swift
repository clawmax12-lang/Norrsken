import SwiftUI

struct DashboardView: View {
    let onNewPreflight: () -> Void

    private let overviewItems = [
        OverviewItem(value: "3", label: "concepts", detail: "Distinct creative hypotheses"),
        OverviewItem(value: "15s", label: "per video", detail: "Launch-ready motion graphics"),
        OverviewItem(value: "3–6", label: "screenshots", detail: "Your product is the source")
    ]

    private let pipelineSteps = [
        PipelineStep(number: "01", title: "Brief", detail: "Add the product, audience, launch goal, and screenshots."),
        PipelineStep(number: "02", title: "Plan", detail: "Shape three concepts with different creative hypotheses."),
        PipelineStep(number: "03", title: "Render", detail: "Turn each concept into a 15-second motion graphics video."),
        PipelineStep(number: "04", title: "Pretest", detail: "Run every variant through the available simulated viewers."),
        PipelineStep(number: "05", title: "Decide", detail: "Review the winner, runner-up, reasons, and launch brief.")
    ]

    init(onNewPreflight: @escaping () -> Void = {}) {
        self.onNewPreflight = onNewPreflight
    }

    var body: some View {
        ZStack {
            DashboardPalette.background
                .ignoresSafeArea()

            ScrollView {
                VStack(spacing: 0) {
                    topBar
                    hero
                    projectOverview
                    pipeline
                    recentBriefs
                    footer
                }
                .frame(maxWidth: 1180)
                .padding(.horizontal, 20)
                .padding(.bottom, 28)
                .frame(maxWidth: .infinity)
            }
            .scrollIndicators(.hidden)
        }
        .preferredColorScheme(.dark)
    }

    private var topBar: some View {
        HStack(spacing: 12) {
            Image(systemName: "triangle.fill")
                .font(.system(size: 17, weight: .bold))
                .foregroundStyle(.white)
                .rotationEffect(.degrees(0))
                .accessibilityHidden(true)

            Text("Preflight")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(.white)

            Text("/ Dashboard")
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(DashboardPalette.secondaryText)

            Spacer()

            HStack(spacing: 7) {
                Circle()
                    .fill(DashboardPalette.tertiaryText)
                    .frame(width: 6, height: 6)
                Text("No active run")
                    .font(.system(size: 11, weight: .medium, design: .monospaced))
                    .foregroundStyle(DashboardPalette.secondaryText)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .background(DashboardPalette.panel, in: Capsule())
            .overlay {
                Capsule()
                    .stroke(DashboardPalette.border, lineWidth: 1)
            }
        }
        .padding(.vertical, 17)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(DashboardPalette.border)
                .frame(height: 1)
        }
    }

    private var hero: some View {
        ViewThatFits(in: .horizontal) {
            HStack(alignment: .bottom, spacing: 48) {
                heroCopy
                Spacer(minLength: 24)
                newPreflightButton
            }

            VStack(alignment: .leading, spacing: 28) {
                heroCopy
                newPreflightButton
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 56)
    }

    private var heroCopy: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("LAUNCH DECISION SYSTEM")
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .tracking(1.4)
                .foregroundStyle(DashboardPalette.tertiaryText)

            Text("Know what to launch\nbefore you launch.")
                .font(.system(size: 42, weight: .semibold, design: .default))
                .tracking(-1.6)
                .foregroundStyle(.white)
                .fixedSize(horizontal: false, vertical: true)
                .minimumScaleFactor(0.78)

            Text("Turn a focused product brief into three motion graphics videos, pretest every variant, and leave with a winner and a launch brief.")
                .font(.system(size: 15, weight: .regular))
                .foregroundStyle(DashboardPalette.secondaryText)
                .lineSpacing(4)
                .frame(maxWidth: 640, alignment: .leading)
        }
    }

    private var newPreflightButton: some View {
        Button(action: onNewPreflight) {
            HStack(spacing: 28) {
                Text("New preflight")
                    .font(.system(size: 14, weight: .semibold))
                Image(systemName: "arrow.up.right")
                    .font(.system(size: 12, weight: .semibold))
            }
            .foregroundStyle(.black)
            .padding(.horizontal, 18)
            .frame(height: 46)
            .background(.white, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("new-preflight-button")
    }

    private var projectOverview: some View {
        DashboardSection(title: "Project overview", eyebrow: "WHAT YOU'LL MAKE") {
            LazyVGrid(
                columns: [GridItem(.adaptive(minimum: 300), spacing: 12)],
                spacing: 12
            ) {
                ForEach(overviewItems) { item in
                    VStack(alignment: .leading, spacing: 20) {
                        HStack(alignment: .firstTextBaseline, spacing: 7) {
                            Text(item.value)
                                .font(.system(size: 28, weight: .semibold, design: .monospaced))
                                .foregroundStyle(.white)
                            Text(item.label)
                                .font(.system(size: 12, weight: .medium))
                                .foregroundStyle(DashboardPalette.tertiaryText)
                        }

                        Text(item.detail)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundStyle(DashboardPalette.secondaryText)
                    }
                    .frame(maxWidth: .infinity, minHeight: 104, alignment: .leading)
                    .padding(18)
                    .dashboardPanel()
                }
            }
        }
    }

    private var pipeline: some View {
        DashboardSection(title: "How a preflight works", eyebrow: "THE PIPELINE") {
            LazyVGrid(
                columns: [GridItem(.adaptive(minimum: 180), spacing: 12)],
                spacing: 12
            ) {
                ForEach(pipelineSteps) { step in
                    VStack(alignment: .leading, spacing: 0) {
                        HStack {
                            Text(step.number)
                                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                .foregroundStyle(DashboardPalette.tertiaryText)
                            Spacer()
                            Circle()
                                .stroke(DashboardPalette.borderStrong, lineWidth: 1)
                                .frame(width: 8, height: 8)
                        }

                        Spacer(minLength: 26)

                        Text(step.title)
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundStyle(.white)
                            .padding(.bottom, 8)

                        Text(step.detail)
                            .font(.system(size: 12, weight: .regular))
                            .foregroundStyle(DashboardPalette.secondaryText)
                            .lineSpacing(3)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .frame(maxWidth: .infinity, minHeight: 150, alignment: .leading)
                    .padding(17)
                    .dashboardPanel()
                }
            }
        }
    }

    private var recentBriefs: some View {
        DashboardSection(title: "Recent briefs", eyebrow: "PROJECTS") {
            ViewThatFits(in: .horizontal) {
                HStack(spacing: 24) {
                    recentBriefsCopy
                    Spacer(minLength: 24)
                    compactNewPreflightButton
                }

                VStack(alignment: .leading, spacing: 22) {
                    recentBriefsCopy
                    compactNewPreflightButton
                }
            }
            .padding(22)
            .frame(maxWidth: .infinity, minHeight: 132, alignment: .leading)
            .dashboardPanel()
        }
    }

    private var recentBriefsCopy: some View {
        HStack(spacing: 16) {
            Image(systemName: "doc.text")
                .font(.system(size: 16, weight: .medium))
                .foregroundStyle(DashboardPalette.tertiaryText)
                .frame(width: 40, height: 40)
                .background(DashboardPalette.elevated, in: RoundedRectangle(cornerRadius: 7))
                .overlay {
                    RoundedRectangle(cornerRadius: 7)
                        .stroke(DashboardPalette.border, lineWidth: 1)
                }

            VStack(alignment: .leading, spacing: 6) {
                Text("No briefs yet")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(.white)
                Text("Your first brief will appear here after you start a preflight.")
                    .font(.system(size: 12))
                    .foregroundStyle(DashboardPalette.secondaryText)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var compactNewPreflightButton: some View {
        Button(action: onNewPreflight) {
            Label("Create first brief", systemImage: "plus")
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(.white)
                .padding(.horizontal, 14)
                .frame(height: 38)
                .background(DashboardPalette.elevated, in: RoundedRectangle(cornerRadius: 7))
                .overlay {
                    RoundedRectangle(cornerRadius: 7)
                        .stroke(DashboardPalette.borderStrong, lineWidth: 1)
                }
        }
        .buttonStyle(.plain)
    }

    private var footer: some View {
        HStack {
            Text("PREFLIGHT")
                .font(.system(size: 10, weight: .semibold, design: .monospaced))
                .tracking(1.2)
            Spacer()
            Text("PRETEST BEFORE YOU SPEND")
                .font(.system(size: 10, weight: .medium, design: .monospaced))
        }
        .foregroundStyle(DashboardPalette.tertiaryText)
        .padding(.top, 32)
    }
}

struct NewPreflightEntryView: View {
    @Environment(\.dismiss) private var dismiss

    private let requirements = [
        BriefRequirement(icon: "text.alignleft", title: "A focused product brief", detail: "Product name, a one-line description, audience, and launch goal."),
        BriefRequirement(icon: "photo.on.rectangle.angled", title: "3–6 product screenshots", detail: "Use real screens from the product you are preparing to launch."),
        BriefRequirement(icon: "scope", title: "One clear goal", detail: "Choose signups, downloads, understanding, or purchase.")
    ]

    var body: some View {
        NavigationStack {
            ZStack {
                DashboardPalette.background
                    .ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: 28) {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("NEW PREFLIGHT")
                                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                .tracking(1.3)
                                .foregroundStyle(DashboardPalette.tertiaryText)
                            Text("Start with the brief.")
                                .font(.system(size: 30, weight: .semibold))
                                .tracking(-0.8)
                                .foregroundStyle(.white)
                            Text("Bring the source material below. Preflight uses it to plan three truthful creative concepts without inventing product claims.")
                                .font(.system(size: 14))
                                .foregroundStyle(DashboardPalette.secondaryText)
                                .lineSpacing(4)
                        }

                        VStack(spacing: 10) {
                            ForEach(requirements) { requirement in
                                HStack(alignment: .top, spacing: 14) {
                                    Image(systemName: requirement.icon)
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundStyle(.white)
                                        .frame(width: 34, height: 34)
                                        .background(DashboardPalette.elevated, in: RoundedRectangle(cornerRadius: 7))

                                    VStack(alignment: .leading, spacing: 5) {
                                        Text(requirement.title)
                                            .font(.system(size: 13, weight: .semibold))
                                            .foregroundStyle(.white)
                                        Text(requirement.detail)
                                            .font(.system(size: 12))
                                            .foregroundStyle(DashboardPalette.secondaryText)
                                            .lineSpacing(3)
                                    }

                                    Spacer(minLength: 0)
                                }
                                .padding(16)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .dashboardPanel()
                            }
                        }

                        Text("Brief intake is the next step in the product flow. No simulation runs from this dashboard entry screen.")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(DashboardPalette.tertiaryText)
                            .lineSpacing(3)
                    }
                    .frame(maxWidth: 620, alignment: .leading)
                    .padding(24)
                    .frame(maxWidth: .infinity)
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Close") {
                        dismiss()
                    }
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(.white)
                }
            }
            .toolbarBackground(DashboardPalette.background, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
        }
        .preferredColorScheme(.dark)
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
    }
}

private struct DashboardSection<Content: View>: View {
    let title: String
    let eyebrow: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(alignment: .firstTextBaseline) {
                Text(title)
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundStyle(.white)
                Spacer()
                Text(eyebrow)
                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                    .tracking(1)
                    .foregroundStyle(DashboardPalette.tertiaryText)
            }

            content
        }
        .padding(.bottom, 44)
    }
}

private struct OverviewItem: Identifiable {
    let id = UUID()
    let value: String
    let label: String
    let detail: String
}

private struct PipelineStep: Identifiable {
    let id = UUID()
    let number: String
    let title: String
    let detail: String
}

private struct BriefRequirement: Identifiable {
    let id = UUID()
    let icon: String
    let title: String
    let detail: String
}

private enum DashboardPalette {
    static let background = Color(red: 10 / 255, green: 10 / 255, blue: 10 / 255)
    static let panel = Color(red: 21 / 255, green: 21 / 255, blue: 21 / 255)
    static let elevated = Color(red: 27 / 255, green: 27 / 255, blue: 27 / 255)
    static let border = Color(red: 42 / 255, green: 42 / 255, blue: 42 / 255)
    static let borderStrong = Color(red: 58 / 255, green: 58 / 255, blue: 58 / 255)
    static let secondaryText = Color(red: 168 / 255, green: 168 / 255, blue: 168 / 255)
    static let tertiaryText = Color(red: 112 / 255, green: 112 / 255, blue: 112 / 255)
}

private extension View {
    func dashboardPanel() -> some View {
        background(DashboardPalette.panel, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .stroke(DashboardPalette.border, lineWidth: 1)
            }
    }
}

#Preview("iPhone") {
    DashboardView()
}

#Preview("iPad", traits: .fixedLayout(width: 1024, height: 1366)) {
    DashboardView()
}
