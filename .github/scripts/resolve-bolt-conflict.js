const fs = require('fs');
const { execSync } = require('child_process');

const BASE_BRANCH = process.env.BASE_BRANCH || 'main';
const HEAD_BRANCH = process.env.HEAD_BRANCH;

if (!HEAD_BRANCH) {
  console.log("Ce déclenchement n'est pas lié à une Pull Request (HEAD_BRANCH manquante). Passage de la résolution de conflits.");
  process.exit(0);
}

const BOLT_PATH = '.jules/bolt.md';

// Fonction pour exécuter une commande shell de manière sécurisée
function runCmd(cmd) {
  try {
    return execSync(cmd, { stdio: 'pipe' }).toString().trim();
  } catch (error) {
    throw new Error(error.stderr ? error.stderr.toString() : error.message);
  }
}

// Fonction pour résoudre le conflit dans le contenu du fichier bolt.md
function resolveBoltConflict(fileContent) {
  const conflictRegex = /<<<<<<< HEAD([\s\S]*?)=======([\s\S]*?)>>>>>>> [^\n]*/g;
  
  let resolvedContent = fileContent;
  let hasConflict = false;

  resolvedContent = resolvedContent.replace(conflictRegex, (match, headBlock, mainBlock) => {
    hasConflict = true;
    const headLines = headBlock.trim();
    const mainLines = mainBlock.trim();

    // Extraire les dates pour trier chronologiquement
    const dateRegex = /## (\d{4}-\d{2}-\d{2})/;
    const headDateMatch = headLines.match(dateRegex);
    const mainDateMatch = mainLines.match(dateRegex);

    if (headDateMatch && mainDateMatch) {
      const headDate = headDateMatch[1];
      const mainDate = mainDateMatch[1];
      if (headDate > mainDate) {
        return `${mainLines}\n\n${headLines}`;
      } else {
        return `${headLines}\n\n${mainLines}`;
      }
    }

    return `${headLines}\n\n${mainLines}`;
  });

  return { resolvedContent, hasConflict };
}

async function run() {
  try {
    console.log(`Vérification des conflits potentiels avec la branche de base : ${BASE_BRANCH}...`);

    // 1. Configurer l'utilisateur Git local pour le commit automatique
    runCmd('git config user.name "github-actions[bot]"');
    runCmd('git config user.email "github-actions[bot]@users.noreply.github.com"');

    // 2. Récupérer la branche de base
    console.log(`Récupération de la branche origin/${BASE_BRANCH}...`);
    runCmd(`git fetch origin ${BASE_BRANCH}`);

    // 3. Tenter de fusionner la branche de base dans la branche actuelle
    console.log(`Tentative de fusion de origin/${BASE_BRANCH}...`);
    try {
      runCmd(`git merge origin/${BASE_BRANCH} --no-edit`);
      console.log("✅ Fusion réussie sans conflit.");
      process.exit(0);
    } catch (mergeError) {
      console.log("⚠️ Conflits détectés lors de la fusion. Analyse de .jules/bolt.md...");
    }

    // 4. Si la fusion a échoué, vérifier s'il s'agit d'un conflit sur bolt.md
    if (!fs.existsSync(BOLT_PATH)) {
      console.log(`Le fichier ${BOLT_PATH} n'existe pas. Impossible de résoudre le conflit automatiquement.`);
      runCmd('git merge --abort');
      process.exit(1);
    }

    const content = fs.readFileSync(BOLT_PATH, 'utf8');
    const { resolvedContent, hasConflict } = resolveBoltConflict(content);

    if (!hasConflict) {
      console.log("❌ Le conflit n'est pas situé dans .jules/bolt.md ou n'a pas pu être résolu automatiquement.");
      runCmd('git merge --abort');
      process.exit(1);
    }

    // 5. Enregistrer le fichier résolu et l'ajouter à git
    console.log("Remplacement du fichier .jules/bolt.md avec la version fusionnée et triée...");
    fs.writeFileSync(BOLT_PATH, resolvedContent, 'utf8');
    runCmd(`git add ${BOLT_PATH}`);

    // 6. Tenter de valider le merge
    try {
      runCmd('git commit -m "ci: resolve merge conflict in .jules/bolt.md by keeping both logs"');
      console.log("✅ Conflit sur .jules/bolt.md résolu et commit de fusion créé.");
    } catch (commitError) {
      console.log("❌ Impossible de valider la fusion. Il reste probablement d'autres conflits dans d'autres fichiers.");
      runCmd('git merge --abort');
      process.exit(1);
    }

    // 7. Pousser la résolution vers la branche distante
    console.log(`Poussée de la résolution vers origin/${HEAD_BRANCH}...`);
    // On utilise l'authentification Git standard fournie par GitHub Actions
    runCmd(`git push origin HEAD:${HEAD_BRANCH}`);
    console.log("🎉 Conflit résolu et poussé sur la branche distante !");

  } catch (error) {
    console.error("Une erreur est survenue lors de la résolution du conflit :", error.message);
    process.exit(1);
  }
}

run();
