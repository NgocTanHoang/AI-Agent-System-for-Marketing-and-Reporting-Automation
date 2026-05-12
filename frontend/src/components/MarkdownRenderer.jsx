import { useEffect, useState } from 'react'
import { marked } from 'marked'

function MarkdownRenderer({ content }) {
  const [html, setHtml] = useState('')

  useEffect(() => {
    if (content) {
      setHtml(marked(content))
    }
  }, [content])

  return (
    <div
      className="text-sm text-on-surface-variant leading-relaxed prose prose-invert max-w-none"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

export default MarkdownRenderer
