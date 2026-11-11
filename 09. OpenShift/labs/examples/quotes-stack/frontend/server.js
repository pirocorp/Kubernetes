"use strict";

const express = require("express");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

const app = express();
const apiUrl = process.env.API_URL || "http://m09-api:8080/quotes";

app.get("/healthz", (_req, res) => res.type("text").send("ok\n"));

app.get("/", async (_req, res) => {
  try {
    const response = await fetch(apiUrl, { signal: AbortSignal.timeout(3000) });
    if (!response.ok) throw new Error("API returned " + response.status);
    const data = await response.json();
    if (!Array.isArray(data.quotes)) throw new Error("Invalid API payload");
    const items = data.quotes.map((q) =>
      React.createElement("li", { key: q.id }, q.text)
    );
    const html = React.createElement(
      "main",
      null,
      React.createElement("h1", null, "OpenShift Quotes - React SSR"),
      React.createElement("p", null, "Python REST + MariaDB"),
      React.createElement("ul", null, ...items)
    );
    res.type("html").send(
      "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\"><title>Quotes</title><body>" +
        renderToStaticMarkup(html) +
      "</body></html>"
    );
  } catch (error) {
    console.error("Backend request failed:", error.message);
    res.status(503).type("text").send("Backend unavailable\n");
  }
});

app.listen(8080, "0.0.0.0", () => console.log("React SSR listening on 8080"));
