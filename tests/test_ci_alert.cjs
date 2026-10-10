'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {monitor, metadata, lastFailure} = require('../.github/scripts/ci-alert.cjs');

function fixture() {
  const issues = [];
  const state = {created:0, updated:0, comments:0};
  const github = {
    paginate: async (_fn, args) => {
      assert.equal(args.state,'open');
      return issues.filter(row => row.state === 'open');
    },
    rest: {issues: {
      listForRepo: () => {},
      create: async args => {
        state.created++;
        issues.push({number: issues.length + 1, ...args, state:'open'});
      },
      update: async args => {
        state.updated++;
        Object.assign(issues.find(x=>x.number===args.issue_number), args);
      },
      createComment: async args => {
        state.comments++;
        assert.ok(issues.find(x=>x.number===args.issue_number));
      },
    }},
  };
  const run = (id, conclusion, attempt=1, branch='main', workflow_id=123) => ({
    id, conclusion, run_attempt:attempt, workflow_id, head_branch:branch,
    name:'NHL test', html_url:`https://github.com/o/r/actions/runs/${id}`,
  });
  const invoke = run => monitor({
    github, context:{payload:{workflow_run:run},repo:{owner:'o',repo:'r'}},
    core:{info:()=>{}},
  });
  return {issues,state,run,invoke};
}

test('creates, deduplicates and closes issues after newer success',async()=>{
  const {issues,state,run,invoke}=fixture();
  assert.equal(await invoke(run(10,'failure')),'opened');
  assert.equal(state.created,1);
  assert.match(issues[0].body,/revue-ci-watch:123/);
  assert.deepEqual(lastFailure(issues[0].body),{runId:10,attempt:1});
  assert.equal(await invoke(run(10,'failure')),'ignored');
  assert.equal(await invoke(run(11,'timed_out')),'updated');
  assert.equal(state.created,1);
  assert.equal(state.comments,1);
  assert.equal(await invoke(run(9,'success')),'ignored');
  assert.equal(issues[0].state,'open');
  assert.equal(await invoke(run(12,'success')),'closed');
  assert.equal(issues[0].state,'closed');
  assert.equal(state.comments,2);
});
test('two workflows produce separate alerts',async()=>{
  const {issues,run,invoke}=fixture();
  assert.equal(await invoke(run(15,'failure',1,'main',123)),'opened');
  assert.equal(await invoke(run(16,'failure',1,'main',456)),'opened');
  assert.equal(issues.length,2);
  assert.equal(await invoke(run(17,'success',1,'main',123)),'closed');
  assert.equal(issues[1].state,'open');
});
test('cancelled, skipped and nonmain workflows are not alerts',async()=>{
  const {issues,run,invoke}=fixture();
  assert.equal(await invoke(run(1,'cancelled')),'ignored');
  assert.equal(await invoke(run(2,'skipped')),'ignored');
  assert.equal(await invoke(run(3,'failure',1,'feature')),'ignored');
  assert.equal(issues.length,0);
});
test('a successful retry of the same run closes the issue',async()=>{
  const {issues,run,invoke}=fixture();
  assert.equal(await invoke(run(9,'failure')),'opened');
  assert.equal(await invoke(run(9,'success',2)),'closed');
  assert.equal(issues[0].state,'closed');
});
test('a previous attempt cannot close a newer failed rerun',async()=>{
  const {issues,run,invoke}=fixture();
  await invoke(run(9,'failure',1));
  await invoke(run(9,'failure',2));
  assert.equal(await invoke(run(9,'success',1)),'ignored');
  assert.equal(issues[0].state,'open');
});
test('invalid event metadata rejected',()=>{
  assert.throws(()=>metadata({id:1}),/metadata/);
});
