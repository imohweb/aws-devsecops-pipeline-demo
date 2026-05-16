const express = require("express");
const { renderTemplatePreview } = require("./demo-risks");

const app = express();
app.use(express.json());

app.get("/", (req, res) => {
  const name = req.query.name || "AWS Community";
  res.send(`<html><body><h1>Hello, ${name}</h1><p>DevSecOps demo app</p></body></html>`);
});

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.post("/template-preview", (req, res) => {
  const template = req.body.template || "2 + 2";
  const result = renderTemplatePreview(template);
  res.json({ preview: result });
});

module.exports = app;

if (require.main === module) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => {
    console.log(`demo app listening on ${port}`);
  });
}
