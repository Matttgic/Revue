'use strict';
/** GitHub Actions failure alert: exactly one open Issue per watched workflow. */
const FAILURE = new Set(['failure', 'timed_out', 'startup_failure', 'action_required']);

function metadata(run) {
  if (!run || !Number.isSafeInteger(run.workflow_id) || !Number.isSafeInteger(run.id)) {
    throw new Error('GitHub workflow metadata is missing');
  }
  const attempt = Number.isSafeInteger(run.run_attempt) ? run.run_attempt : 1;
  return {
    workflowId: run.workflow_id, runId: run.id, attempt,
    marker: `<!-- revue-ci-watch:${run.workflow_id} -->`,
    last: `<!-- revue-ci-last-run:${run.id}:${attempt} -->`,
  };
}

function alertBody(run) {
  const m = metadata(run);
  return [
    `Le workflow **${run.name}** a terminé en échec.`,
    '',
    `- Résultat : **${run.conclusion}**`,
    `- Exécution : ${run.html_url}`,
    `- Branche : ${run.head_branch}`,
    `- Tentative : ${m.attempt}`,
    '',
    'Vérifier les logs dans GitHub Actions puis corriger le problème. Cette issue sera fermée automatiquement après une nouvelle exécution réussie du même workflow.',
    '', m.marker, m.last,
  ].join('\n');
}

function lastFailure(body) {
  const match = (body || '').match(/<!-- revue-ci-last-run:(\d+):(\d+) -->/);
  return match ? {runId: Number(match[1]), attempt: Number(match[2])} : null;
}

async function monitor({github, context, core}) {
  const run = context.payload.workflow_run;
  if (!run || run.head_branch !== 'main') {
    core.info('Ignoring non-main or absent workflow run');
    return 'ignored';
  }
  const m = metadata(run);
  if (!FAILURE.has(run.conclusion) && run.conclusion !== 'success') {
    core.info(`Ignoring workflow result: ${run.conclusion}`);
    return 'ignored';
  }
  const {owner, repo} = context.repo;
  // Paginate to keep deduplication correct even when the repository grows.
  const open = await github.paginate(github.rest.issues.listForRepo, {
    owner, repo, state: 'open', per_page: 100,
  });
  const issue = open.find(row => !row.pull_request && (row.body || '').includes(m.marker));
  const title = `[CI] Échec : ${run.name}`;
  if (FAILURE.has(run.conclusion)) {
    if (!issue) {
      await github.rest.issues.create({owner, repo, title, body: alertBody(run)});
      core.info(`Opened alert for ${run.name}`);
      return 'opened';
    }
    const prev = lastFailure(issue.body);
    if (prev && (prev.runId > m.runId || (prev.runId === m.runId && prev.attempt >= m.attempt))) {
      core.info('Duplicate/outdated failure: no update');
      return 'ignored';
    }
    await github.rest.issues.update({owner, repo, issue_number: issue.number,
      title, body: alertBody(run)});
    await github.rest.issues.createComment({owner, repo, issue_number: issue.number,
      body: `Nouvel échec de **${run.name}** : ${run.html_url} (${run.conclusion}).`});
    core.info(`Updated existing alert #${issue.number}`);
    return 'updated';
  }
  if (!issue) return 'ignored';
  const prev = lastFailure(issue.body);
  if (prev && (m.runId < prev.runId || (m.runId === prev.runId && m.attempt < prev.attempt))) {
    core.info('Older success cannot close newer failure');
    return 'ignored';
  }
  await github.rest.issues.createComment({owner, repo, issue_number: issue.number,
    body: `Résolu : nouvelle exécution réussie du workflow **${run.name}** : ${run.html_url}.`});
  await github.rest.issues.update({owner, repo, issue_number: issue.number, state: 'closed'});
  core.info(`Closed resolved alert #${issue.number}`);
  return 'closed';
}

module.exports = {monitor, metadata, lastFailure, alertBody};
