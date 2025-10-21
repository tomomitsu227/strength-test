import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'あなたの強みを発見 | YouTube強み診断',
  description: '簡単な5分間の診断で、あなたに最適なYouTubeジャンルと成功戦略がわかる',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  )
}