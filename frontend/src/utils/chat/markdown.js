import { encode as HTMLEncode } from "he";
import markdownIt from "markdown-it";
import markdownItKatexPlugin from "./plugins/markdown-katex";
import hljs from "highlight.js";
import "./themes/github-dark.css";
import "./themes/github.css";
import { v4 } from "uuid";

const markdown = markdownIt({
  html: true,
  typographer: true,
  highlight: function (code, lang) {
    const uuid = v4();
    const theme =
      window.localStorage.getItem("theme") === "light"
        ? "github"
        : "github-dark";

    if (lang && hljs.getLanguage(lang)) {
      try {
        return (
          `<div class="whitespace-pre-line w-full max-w-[65vw] hljs ${theme} light:border-solid light:border light:border-gray-700 rounded-lg relative font-mono font-normal text-sm text-slate-200">
            <div class="w-full flex items-center sticky top-0 text-slate-200 light:bg-sky-800 bg-stone-800 px-4 py-2 text-xs font-sans justify-between rounded-t-md -mt-5">
              <div class="flex gap-2">
                <code class="text-xs">${lang || ""}</code>
              </div>
              <button data-code-snippet data-code="code-${uuid}" class="flex items-center gap-x-1">
                <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" class="h-3 w-3" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>
                <p class="text-xs" style="margin: 0px;padding: 0px;">Copy block</p>
              </button>
            </div>
            <pre class="whitespace-pre-wrap px-4 pb-4">` +
          hljs.highlight(code, { language: lang, ignoreIllegals: true }).value +
          "</pre></div>"
        );
      } catch (__) {}
    }

    return (
      `<div class="whitespace-pre-line w-full max-w-[65vw] hljs ${theme} light:border-solid light:border light:border-gray-700 rounded-lg relative font-mono font-normal text-sm text-slate-200">
        <div class="w-full flex items-center sticky top-0 text-slate-200 bg-stone-800 px-4 py-2 text-xs font-sans justify-between rounded-t-md -mt-5">
          <div class="flex gap-2"><code class="text-xs"></code></div>
          <button data-code-snippet data-code="code-${uuid}" class="flex items-center gap-x-1">
            <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" class="h-3 w-3" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>
            <p class="text-xs" style="margin: 0px;padding: 0px;">Copy block</p>
          </button>
        </div>
        <pre class="whitespace-pre-wrap px-4 pb-4">` +
      HTMLEncode(code) +
      "</pre></div>"
    );
  },
});

// Add custom renderer for strong tags to handle theme colors
markdown.renderer.rules.strong_open = () => '<strong class="text-white">';
markdown.renderer.rules.strong_close = () => "</strong>";
markdown.renderer.rules.link_open = (tokens, idx) => {
  const token = tokens[idx];
  const href = token.attrs.find((attr) => attr[0] === "href");
  return `<a href="${href[1]}" target="_blank" rel="noopener noreferrer">`;
};

// Custom renderer for responsive images rendered in markdown
markdown.renderer.rules.image = function (tokens, idx) {
  const token = tokens[idx];
  const srcIndex = token.attrIndex("src");
  let src = token.attrs[srcIndex][1];
  const alt = token.content || "";
  const titleIndex = token.attrIndex("title");
  const title = titleIndex >= 0 ? token.attrs[titleIndex][1] : alt;

  // Handle extracted images from multimodal processing
  // Convert relative paths like "src/extract-images/..." to absolute "/src/extract-images/..."
  if (src.startsWith("src/extract-images/")) {
    src = "/" + src; // Add leading slash -> "/src/extract-images/..."
  } else if (src.startsWith("extract-images/")) {
    src = "/src/" + src; // Add "/src/" prefix -> "/src/extract-images/..."
  } else if (src.startsWith("/extract-images/")) {
    src = "/src" + src; // Convert "/extract-images/" -> "/src/extract-images/..."
  }

  // Render image with responsive wrapper and proper attributes
  return `<div class="w-full max-w-[800px] my-4">
    <img src="${src}" alt="${alt}" title="${title}" class="w-full h-auto rounded-lg shadow-md" loading="lazy" />
    ${title && title !== alt ? `<p class="text-xs text-gray-400 mt-2 italic">${title}</p>` : ''}
  </div>`;
};

// Custom paragraph renderer to prevent wrapping <img> tags in <p> tags
const defaultParagraphOpen = markdown.renderer.rules.paragraph_open ||
  function(tokens, idx, options, env, self) {
    return self.renderToken(tokens, idx, options);
  };

const defaultParagraphClose = markdown.renderer.rules.paragraph_close ||
  function(tokens, idx, options, env, self) {
    return self.renderToken(tokens, idx, options);
  };

markdown.renderer.rules.paragraph_open = function(tokens, idx, options, env, self) {
  // Check if paragraph contains only an img tag (inline HTML or markdown image)
  const nextToken = tokens[idx + 1];
  if (nextToken && nextToken.type === 'inline') {
    // Check for inline HTML img tags
    if (nextToken.content) {
      const imgTagPattern = /^\s*<img[^>]*>\s*$/i;
      if (imgTagPattern.test(nextToken.content)) {
        return '';
      }
    }

    // Check for markdown images (rendered through image token)
    if (nextToken.children && nextToken.children.length === 1 &&
        nextToken.children[0].type === 'image') {
      return '';
    }
  }
  return defaultParagraphOpen(tokens, idx, options, env, self);
};

markdown.renderer.rules.paragraph_close = function(tokens, idx, options, env, self) {
  // Check if paragraph contains only an img tag (inline HTML or markdown image)
  const prevToken = tokens[idx - 1];
  if (prevToken && prevToken.type === 'inline') {
    // Check for inline HTML img tags
    if (prevToken.content) {
      const imgTagPattern = /^\s*<img[^>]*>\s*$/i;
      if (imgTagPattern.test(prevToken.content)) {
        return '';
      }
    }

    // Check for markdown images (rendered through image token)
    if (prevToken.children && prevToken.children.length === 1 &&
        prevToken.children[0].type === 'image') {
      return '';
    }
  }
  return defaultParagraphClose(tokens, idx, options, env, self);
};

markdown.use(markdownItKatexPlugin);

export default function renderMarkdown(text = "") {
  return markdown.render(text);
}
