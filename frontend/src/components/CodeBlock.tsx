import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface CodeBlockProps {
  inline?: boolean
  className?: string
  children: React.ReactNode
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ inline, className, children }) => {
  const match = /language-(\w+)/.exec(className || '')
  const code = String(children).replace(/\n$/, '')

  if (inline) {
    return <code className={className}>{code}</code>
  }

  return (
    <SyntaxHighlighter
      language={match ? match[1] : undefined}
      style={oneDark}
      PreTag="div"
      wrapLongLines
      customStyle={{ margin: 0, borderRadius: '0.5rem', padding: '1rem' }}
    >
      {code}
    </SyntaxHighlighter>
  )
}
