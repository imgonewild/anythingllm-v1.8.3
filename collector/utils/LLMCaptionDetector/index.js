/**
 * LLM-based Caption Detector
 * Uses LLM to identify image captions from text - language and format agnostic
 */

const CAPTION_DETECTION_PROMPT = `You are analyzing text extracted from a document page that contains an image.
Your task is to identify if any of the following lines is an image caption.

A caption typically:
- Describes or labels an image/figure/diagram/chart/table
- Often starts with a label word (in any language) followed by a number
- Is usually short (under 200 characters)
- May contain a colon or dash separating the label from the description

Lines to analyze:
{LINES}

If you find a caption, respond with ONLY the caption text, nothing else.
If no caption is found, respond with exactly: NO_CAPTION_FOUND

Your response:`;

/**
 * Detect caption using Ollama
 */
async function detectCaptionWithOllama(candidateLines, options = {}) {
  const baseUrl = options.ollamaBaseUrl || process.env.OLLAMA_BASE_PATH || 'http://127.0.0.1:11434';
  const model = options.ollamaModel || process.env.OLLAMA_MODEL_PREF || 'llama3.2';

  try {
    const prompt = CAPTION_DETECTION_PROMPT.replace('{LINES}', candidateLines.join('\n'));

    const response = await fetch(`${baseUrl}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        prompt,
        stream: false,
        options: {
          temperature: 0.1,
          num_predict: 256
        }
      })
    });

    if (!response.ok) {
      console.warn(`Ollama request failed: ${response.status}`);
      return null;
    }

    const data = await response.json();
    const result = data.response?.trim();

    if (result && result !== 'NO_CAPTION_FOUND') {
      return result;
    }
    return null;
  } catch (error) {
    console.warn(`Ollama caption detection failed: ${error.message}`);
    return null;
  }
}

/**
 * Detect caption using OpenAI-compatible API
 */
async function detectCaptionWithOpenAI(candidateLines, options = {}) {
  const baseUrl = options.openaiBaseUrl || process.env.OPENAI_BASE_PATH || 'https://api.openai.com/v1';
  const apiKey = options.openaiApiKey || process.env.OPEN_AI_KEY;
  const model = options.openaiModel || process.env.OPEN_MODEL_PREF || 'gpt-4o-mini';

  if (!apiKey) {
    console.warn('No OpenAI API key available for caption detection');
    return null;
  }

  try {
    const prompt = CAPTION_DETECTION_PROMPT.replace('{LINES}', candidateLines.join('\n'));

    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.1,
        max_tokens: 256
      })
    });

    if (!response.ok) {
      console.warn(`OpenAI request failed: ${response.status}`);
      return null;
    }

    const data = await response.json();
    const result = data.choices?.[0]?.message?.content?.trim();

    if (result && result !== 'NO_CAPTION_FOUND') {
      return result;
    }
    return null;
  } catch (error) {
    console.warn(`OpenAI caption detection failed: ${error.message}`);
    return null;
  }
}

/**
 * Main caption detection function
 * Tries Ollama first, falls back to OpenAI if configured
 * @param {string[]} candidateLines - Array of text lines that might contain a caption
 * @param {Object} options - Configuration options
 * @returns {Promise<string|null>} - The detected caption or null
 */
async function detectCaption(candidateLines, options = {}) {
  if (!candidateLines || candidateLines.length === 0) {
    return null;
  }

  // Filter out empty lines and very long lines (unlikely to be captions)
  const filteredLines = candidateLines
    .map(l => l.trim())
    .filter(l => l.length > 3 && l.length < 300);

  if (filteredLines.length === 0) {
    return null;
  }

  // Limit to first 20 lines to keep prompt small
  const linesToAnalyze = filteredLines.slice(0, 20);

  // Check which LLM provider to use
  const provider = options.captionLLMProvider || process.env.CAPTION_LLM_PROVIDER || 'ollama';

  if (provider === 'openai') {
    return await detectCaptionWithOpenAI(linesToAnalyze, options);
  }

  // Default: try Ollama first, then OpenAI as fallback
  let caption = await detectCaptionWithOllama(linesToAnalyze, options);

  if (!caption && process.env.OPEN_AI_KEY) {
    caption = await detectCaptionWithOpenAI(linesToAnalyze, options);
  }

  return caption;
}

/**
 * Check if LLM caption detection is available
 */
async function isLLMCaptionDetectionAvailable() {
  // Check if Ollama is available
  try {
    const ollamaUrl = process.env.OLLAMA_BASE_PATH || 'http://127.0.0.1:11434';
    const response = await fetch(`${ollamaUrl}/api/tags`, {
      method: 'GET',
      signal: AbortSignal.timeout(2000)
    });
    if (response.ok) {
      return { available: true, provider: 'ollama' };
    }
  } catch (e) {
    // Ollama not available
  }

  // Check if OpenAI is configured
  if (process.env.OPEN_AI_KEY) {
    return { available: true, provider: 'openai' };
  }

  return { available: false, provider: null };
}

module.exports = {
  detectCaption,
  detectCaptionWithOllama,
  detectCaptionWithOpenAI,
  isLLMCaptionDetectionAvailable,
  CAPTION_DETECTION_PROMPT
};
