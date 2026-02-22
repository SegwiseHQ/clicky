cask "clicky" do
  version "0.1.0"

  on_arm do
    sha256 "REPLACE_WITH_ARM64_SHA256"
    url "https://github.com/SegwiseHQ/clicky/releases/download/v#{version}/clicky-macos-arm64.zip"
  end

  on_intel do
    sha256 "REPLACE_WITH_X86_64_SHA256"
    url "https://github.com/SegwiseHQ/clicky/releases/download/v#{version}/clicky-macos-x86_64.zip"
  end

  name "Clicky"
  desc "Free, lightweight ClickHouse desktop client"
  homepage "https://github.com/SegwiseHQ/clicky"

  app "clicky.app"

  zap trash: [
    "~/Library/Application Support/clicky",
  ]
end
