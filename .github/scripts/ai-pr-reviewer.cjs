const https = require('https');

// Configuration from environment variables
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const GITHUB_REPOSITORY = process.env.GITHUB_REPOSITORY;
const PR_NUMBER = process.env.GITHUB_PR_NUMBER;
const GEMINI_MODEL = process.env.GEMINI_MODEL || 'gemini-2.5-flash';

if (!GITHUB_TOKEN || !GEMINI_API_KEY || !GITHUB_REPOSITORY || !PR_NUMBER) {
  console.error("Missing env vars: GITHUB_TOKEN, GEMINI_API_KEY, GITHUB_REPOSITORY, GITHUB_PR_NUMBER");
  process.exit(1);
}

const SUPPORTED_EXTENSIONS = [
  '.js', '.ts', '.jsx', '.tsx', '.py', '.sh', '.yml', '.yaml',
  '.json', '.css', '.html', '.go', '.rs', '.c', '.cpp', '.h',
  '.conf', '.ini', '.md', '.toml'
];

const IGNORED_FILES = [
  'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'composer.lock',
  'AGENTS.md', 'task.md', 'implementation_plan.md', 'walkthrough.md'
];

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000;

// HTTPS request helper with retry and exponential backoff
function makeRequest(options, postData = null, retries = MAX_RETRIES) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({ data, headers: res.headers });
        } else if (res.statusCode === 429 && retries > 0) {
          const delay = BASE_DELAY_MS * Math.pow(2, MAX_RETRIES - retries);
          console.warn(`Rate limited. Retrying in ${delay}ms...`);
          setTimeout(() => {
            makeRequest(options, postData, retries - 1).then(resolve).catch(reject);
          }, delay);
        } else if (res.statusCode >= 500 && retries > 0) {
          const delay = BASE_DELAY_MS * Math.pow(2, MAX_RETRIES - retries);
          console.warn(`Server error ${res.statusCode}. Retrying in ${delay}ms...`);
          setTimeout(() => {
            makeRequest(options, postData, retries - 1).then(resolve).catch(reject);
          }, delay);
        } else {
          reject(new Error(`Status ${res.statusCode}: ${data}`));
        }
      });
    });
    req.on('error', (err) => {
      if (retries > 0) {
        const delay = BASE_DELAY_MS * Math.pow(2, MAX_RETRIES - retries);
        setTimeout(() => {
          makeRequest(options, postData, retries - 1).then(resolve).catch(reject);
        }, delay);
      } else {
        reject(err);
      }
    });
    if (postData) {
      req.write(typeof postData === 'string' ? postData : JSON.stringify(postData));
    }
    req.end();
  });
}

// Fetch all pages of PR files (handles pagination)
async function fetchAllPRFiles() {
  const allFiles = [];
  let page = 1;

  while (true) {
    const options = {
      hostname: 'api.github.com',
      path: `/repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}/files?per_page=100&page=${page}`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'AI-PR-Reviewer-Action'
      }
    };

    const { data } = await makeRequest(options);
    const files = JSON.parse(data);

    if (files.length === 0) break;
    allFiles.push(...files);

    if (files.length < 100) break;
    page++;
  }

  return allFiles;
}

// Extract added line numbers from a unified diff patch
function getAddedLines(patch) {
  if (!patch) return [];
  const lines = patch.split('\n');
  const addedLines = [];
  let currentNewLineNum = 0;

  for (const line of lines) {
    const chunkHeader = line.match(/^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (chunkHeader) {
      currentNewLineNum = parseInt(chunkHeader[1], 10);
      continue;
    }

    if (line.startsWith('+') && !line.startsWith('+++')) {
      addedLines.push(currentNewLineNum);
      currentNewLineNum++;
    } else if (line.startsWith('-')) {
      // Deleted line — skip
    } else {
      currentNewLineNum++;
    }
  }
  return addedLines;
}

async function run() {
  try {
    console.log(`AI review for PR #${PR_NUMBER} on ${GITHUB_REPOSITORY} (model: ${GEMINI_MODEL})`);

    // 1. Get PR details for head SHA
    const prDetailsOptions = {
      hostname: 'api.github.com',
      path: `/repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'AI-PR-Reviewer-Action'
      }
    };
    const { data: prDetailsRaw } = await makeRequest(prDetailsOptions);
    const prDetails = JSON.parse(prDetailsRaw);
    const commitSha = prDetails.head.sha;
    console.log(`Head SHA: ${commitSha}`);

    // 2. Fetch all modified files (paginated)
    const files = await fetchAllPRFiles();

    const filesToAnalyze = files.filter(file => {
      if (IGNORED_FILES.some(ignored => file.filename.endsWith(ignored))) return false;
      return SUPPORTED_EXTENSIONS.some(ext => file.filename.endsWith(ext)) && !!file.patch;
    });

    if (filesToAnalyze.length === 0) {
      console.log("No analyzable code files found.");
      return;
    }

    console.log(`${filesToAnalyze.length} files retained for analysis.`);

    // 3. Prepare diff data for Gemini
    const fileDiffData = filesToAnalyze.map(file => ({
      filename: file.filename,
      patch: file.patch,
      validLinesForComments: getAddedLines(file.patch)
    }));

    // 4. Call Gemini API
    const systemInstruction = `Tu es un expert en revue de code (ingénieur logiciel principal). Analyse les modifications d'une Pull Request et génère une revue technique constructive et précise.

Consignes :
1. Génère des commentaires ciblés uniquement si nécessaire (bugs, failles de sécurité, optimisations majeures, mauvaise gestion d'erreurs, lisibilité).
2. Chaque commentaire DOIT avoir un numéro de ligne ('line') présent dans 'validLinesForComments' du fichier correspondant. Ne commente jamais sur une ligne hors de cette liste.
3. Rédige en français, de manière claire et technique. Propose du code de correction en bloc markdown si pertinent.
4. Verdict global dans le champ 'verdict' :
   - 'APPROVE' : Code excellent, prêt à fusionner (aucun commentaire requis).
   - 'COMMENT' : Suggestions mineures, non bloquantes.
   - 'REQUEST_CHANGES' : Bugs sérieux, failles de sécurité, ou problèmes de performance bloquants.
5. Réponds en JSON strictement conforme à ce schéma :
{
  "verdict": "APPROVE" | "COMMENT" | "REQUEST_CHANGES",
  "summary": "Résumé global de la revue.",
  "comments": [
    {
      "path": "chemin/du/fichier.js",
      "line": 42,
      "body": "Explication du problème ou suggestion."
    }
  ]
}`;

    const promptUser = `Fichiers modifiés et diffs pour la PR #${PR_NUMBER} :
${JSON.stringify(fileDiffData, null, 2)}`;

    const geminiPayload = {
      contents: [{ parts: [{ text: promptUser }] }],
      systemInstruction: { parts: [{ text: systemInstruction }] },
      generationConfig: { responseMimeType: "application/json" }
    };

    const geminiUrl = new URL(
      `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_API_KEY}`
    );

    const geminiOptions = {
      hostname: geminiUrl.hostname,
      path: geminiUrl.pathname + geminiUrl.search,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    };

    console.log(`Sending to Gemini (${GEMINI_MODEL})...`);
    const { data: geminiResponseRaw } = await makeRequest(geminiOptions, geminiPayload);
    const geminiResponse = JSON.parse(geminiResponseRaw);

    const responseText = geminiResponse.candidates[0].content.parts[0].text;
    const reviewResult = JSON.parse(responseText);

    console.log(`Verdict: ${reviewResult.verdict}`);
    console.log(`Summary: ${reviewResult.summary}`);
    console.log(`Comments: ${reviewResult.comments ? reviewResult.comments.length : 0}`);

    // Filter comments to valid diff lines only
    const validComments = [];
    if (reviewResult.comments && Array.isArray(reviewResult.comments)) {
      for (const comment of reviewResult.comments) {
        const fileData = fileDiffData.find(f => f.filename === comment.path);
        if (fileData && fileData.validLinesForComments.includes(Number(comment.line))) {
          validComments.push({
            path: comment.path,
            line: Number(comment.line),
            side: 'RIGHT',
            body: comment.body
          });
        } else {
          console.warn(`Skipped invalid comment: ${comment.path}:${comment.line} (not in diff)`);
        }
      }
    }

    // 5. Submit review to GitHub
    const reviewPayload = {
      commit_id: commitSha,
      body: `### 🤖 Revue automatique par l'IA (${GEMINI_MODEL})

**Verdict :** ${reviewResult.verdict === 'APPROVE' ? '✅ Approuvé' : reviewResult.verdict === 'REQUEST_CHANGES' ? '❌ Changements demandés' : '💬 Commentaires'}

${reviewResult.summary}

_Revue générée automatiquement._`,
      event: reviewResult.verdict,
      comments: validComments
    };

    const submitReviewOptions = {
      hostname: 'api.github.com',
      path: `/repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}/reviews`,
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'AI-PR-Reviewer-Action',
        'Content-Type': 'application/json'
      }
    };

    await makeRequest(submitReviewOptions, reviewPayload);
    console.log("Review published successfully.");

  } catch (error) {
    console.error("AI review failed:", error);
    process.exit(1);
  }
}

run();
