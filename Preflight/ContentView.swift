import SwiftUI

struct ContentView: View {
    @State private var isPresentingNewPreflight = false

    var body: some View {
        DashboardView {
            isPresentingNewPreflight = true
        }
        .sheet(isPresented: $isPresentingNewPreflight) {
            NewPreflightEntryView()
        }
    }
}

#Preview {
    ContentView()
}
