'use strict';
let queries = null;
let tree = null;

function main()
{
  queries = rawReport.test_cases[0].queries[0].queries;
  tree = traceTree(window.rawReport);
}

function traceTree(queries)
{
  let tree = { trace: '<root>', queries: [], children: {}, total: 0 };

  queries.forEach((query) => {
    query.stacktrace = query.stacktrace.map(getFormattedTrace);
  });

  queries.forEach((query) => {
    addToTree(tree, query, 0, query.stacktrace.length);
  });

  tree = squashTree(tree);
  return tree;
}

function squashTree(tree)
{
  let childrenKeys = Object.keys(tree.children);

  var squashedChilds = {};
  childrenKeys.forEach((key) => {
    squashedChilds[key] = squashTree(tree.children[key]);
  });
  tree.children = squashedChilds;

  if(childrenKeys.length != 1)
  {
    return tree;
  }
  else {
    let childTree = tree.children[childrenKeys[0]];

    return {
      trace: [tree.trace].concat(childTree.trace),
      queries: tree.queries,
      total: tree.total,
      children: childTree.children
    };
  }
}

function getFormattedTrace(traceElement)
{
  const pathReplacements = [
    [ '/home/igui/envs/profit-tools-django/lib/python3.4/site-packages/', '' ],
    [ '/home/igui/src/profit-tools/planning-view/app/', 'app/' ],
  ];

  let filePath = traceElement[0];

  for(var idx in pathReplacements)
  {
    filePath = filePath.replace(
      pathReplacements[idx][0],
      pathReplacements[idx][1]
    );
  }

  return filePath + ':' + traceElement[1] + '>' + traceElement[2];
}

function formatSQL(sql)
{
  return sql.replace(/\"/g, '');
}

function addToTree(tree, query, firstIdx, lastIdx)
{
  if(firstIdx >= lastIdx)
  {
    return;
  }

  let traceElement = query.stacktrace[firstIdx];
  let child = tree.children[traceElement];

  if(!child)
  {
    child = { trace: traceElement, queries: [], children: {}, total: 0 };
    tree.children[traceElement] = child;
  }

  addToTree(child, query, firstIdx+1, lastIdx);

  const sql = formatSQL(query.sql);
  tree.queries.push(sql);
  tree.total++;
}

main();

