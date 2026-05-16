const { exec } = require("child_process");

function renderTemplatePreview(template) {
  return eval(template);
}

function runDemoCommand(command) {
  exec(command, () => {});
}

module.exports = {
  renderTemplatePreview,
  runDemoCommand
};

