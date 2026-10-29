const express = require("express");
const session = require("express-session");

console.log("=========================================");
console.log("🚀 STARTING CSRF & PRODUCTION LOGIC TESTS");
console.log("=========================================\n");

const app = express();
app.set("trust proxy", 1);

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Mock session setup for testing
app.use(
  session({
    secret: "test_secret_123",
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false, sameSite: "lax" }
  })
);

// CSRF Auto-injection middleware (Same as app.js)
app.use((req, res, next) => {
  if (req.session) {
    if (!req.session.csrfToken) {
      const crypto = require("crypto");
      req.session.csrfToken = crypto.randomBytes(24).toString("hex");
    }
    res.locals.csrfToken = req.session.csrfToken;
  }

  const originalRender = res.render;
  res.render = function (view, options, callback) {
    const token = req.session?.csrfToken;
    if (token) {
      res.locals.csrfToken = token;
    }

    // Mock rendering for testing
    let html = `<html><body><form action="/documents/upload" method="POST" enctype="multipart/form-data"><button>Upload</button></form></body></html>`;

    if (html && token) {
      html = html.replace(
        /(<form[^>]*method=["']POST["'][^>]*>)/gi,
        `$1\n<input type="hidden" name="_csrf" value="${token}">`
      );

      html = html.replace(
        /<form([^>]*\bmethod=["']POST["'][^>]*)>/gi,
        (match, formInner) => {
          if (/action=["'][^"']*["']/i.test(formInner)) {
            return match.replace(/action=["']([^"']*)["']/i, (actMatch, url) => {
              if (url.includes("_csrf=")) return actMatch;
              const delimiter = url.includes("?") ? "&" : "?";
              return `action="${url}${delimiter}_csrf=${token}"`;
            });
          } else {
            return `<form${formInner} action="?_csrf=${token}">`;
          }
        }
      );
    }

    if (callback) callback(null, html);
    else res.send(html);
  };

  next();
});

// CSRF Validator middleware (Same as app.js)
app.use((req, res, next) => {
  if (["POST", "PUT", "DELETE", "PATCH"].includes(req.method)) {
    const isJson =
      req.headers.accept?.includes("application/json") ||
      req.headers["content-type"]?.includes("application/json") ||
      req.headers["x-requested-with"] === "XMLHttpRequest" ||
      req.path.startsWith("/api/") ||
      req.body?.format === "json" ||
      req.query?.format === "json";

    if (isJson) return next();

    const token =
      req.body?._csrf ||
      req.query?._csrf ||
      req.headers["x-csrf-token"] ||
      req.headers["csrf-token"] ||
      req.headers["x-xsrf-token"];

    if (!token || !req.session?.csrfToken || token !== req.session.csrfToken) {
      return res.status(403).send("CSRF_BLOCKED");
    }
  }
  next();
});

// Test routes
app.get("/test-render", (req, res) => {
  res.render("dummy");
});

app.post("/documents/upload", (req, res) => {
  res.send("UPLOAD_SUCCESS");
});

app.post("/api/test", (req, res) => {
  res.json({ status: "API_SUCCESS" });
});

// Run assertions
let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`✅ PASSED: ${message}`);
    passed++;
  } else {
    console.error(`❌ FAILED: ${message}`);
    failed++;
  }
}

// 1. Test Trust Proxy setting
assert(app.get("trust proxy") === 1, "Express 'trust proxy' is set to 1");

// Listen on random port for testing
const server = app.listen(0, async () => {
  const port = server.address().port;
  const baseUrl = `http://127.0.0.1:${port}`;

  try {
    // Test 1: Render view and check CSRF HTML injection
    const resRender = await fetch(`${baseUrl}/test-render`);
    const cookieHeader = resRender.headers.get("set-cookie");
    const htmlText = await resRender.text();

    assert(htmlText.includes('name="_csrf"'), "CSRF hidden input tag auto-injected into form");
    assert(htmlText.includes('action="/documents/upload?_csrf='), "CSRF query parameter auto-injected into form action attribute");

    // Extract CSRF token from HTML
    const match = htmlText.match(/value="([a-f0-9]+)"/);
    const token = match ? match[1] : null;
    assert(token !== null && token.length === 48, "Generated 24-byte hex CSRF token successfully");

    // Test 2: Valid CSRF via query param (Multipart form simulation)
    const resUpload = await fetch(`${baseUrl}/documents/upload?_csrf=${token}`, {
      method: "POST",
      headers: { cookie: cookieHeader }
    });
    const uploadText = await resUpload.text();
    assert(uploadText === "UPLOAD_SUCCESS", "Multipart form POST with query param _csrf succeeded");

    // Test 3: Invalid CSRF token blocked
    const resBlocked = await fetch(`${baseUrl}/documents/upload?_csrf=invalid_token`, {
      method: "POST",
      headers: { cookie: cookieHeader }
    });
    const blockedText = await resBlocked.text();
    assert(blockedText === "CSRF_BLOCKED" && resBlocked.status === 403, "Invalid CSRF token correctly blocked with HTTP 403");

    // Test 4: JSON API bypass check
    const resApi = await fetch(`${baseUrl}/api/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    const apiJson = await resApi.json();
    assert(apiJson.status === "API_SUCCESS", "JSON API POST correctly bypassed CSRF token check");

    console.log("\n=========================================");
    console.log(`📊 TEST SUMMARY: Passed ${passed}, Failed ${failed}`);
    console.log("=========================================");

    server.close(() => {
      process.exit(failed > 0 ? 1 : 0);
    });
  } catch (err) {
    console.error("Test execution error:", err);
    server.close(() => process.exit(1));
  }
});
