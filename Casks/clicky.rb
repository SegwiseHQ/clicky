cask "clicky" do
  version "0.1.0"
  sha256 "REPLACE_WITH_ARM64_SHA256"

  url "https://github.com/SegwiseHQ/clicky/releases/download/v#{version}/clicky-macos-arm64.zip"
  name "Clicky"
  desc "Free, lightweight ClickHouse desktop client"
  homepage "https://github.com/SegwiseHQ/clicky"

  depends_on arch: :arm64

  app "clicky.app"

  postflight do
    system_command "/usr/bin/xattr",
                   args: ["-cr", "#{appdir}/clicky.app"]
  end

  zap trash: [
    "~/Library/Application Support/clicky",
  ]
end
