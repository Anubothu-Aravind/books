// Endpoint specifications
const ENDPOINTS = {
  versions: {
    route: "/api/versions",
    description: "List all ingested Bible translations and metadata.",
    params: []
  },
  books: {
    route: "/api/books",
    description: "List all unique books of the Bible and testaments.",
    params: []
  },
  verse: {
    route: "/api/verse",
    description: "Fetch specific verse text and labels.",
    params: [
      { name: "version", type: "text", default: "KJV", placeholder: "e.g. KJV, ASV" },
      { name: "book", type: "text", default: "Genesis", placeholder: "e.g. Genesis, Matthew" },
      { name: "chapter", type: "number", default: "1", placeholder: "e.g. 1" },
      { name: "verse", type: "number", default: "1", placeholder: "e.g. 1" }
    ]
  },
  chapter: {
    route: "/api/chapter",
    description: "Fetch all verses in a chapter.",
    params: [
      { name: "version", type: "text", default: "KJV", placeholder: "e.g. KJV, ASV" },
      { name: "book", type: "text", default: "Genesis", placeholder: "e.g. Genesis, Matthew" },
      { name: "chapter", type: "number", default: "1", placeholder: "e.g. 1" }
    ]
  },
  places: {
    route: "/api/geography/places",
    description: "List all geography places, optionally filtered by type.",
    params: [
      { name: "type", type: "select", default: "", options: ["", "settlement", "region", "water", "mountain", "valley", "desert"] }
    ]
  },
  place: {
    route: "/api/geography/place",
    description: "Fetch details of a specific geography place by ID.",
    params: [
      { name: "id", type: "text", default: "jerusalem", placeholder: "e.g. jerusalem, jordan-river" }
    ]
  },
  crossref: {
    route: "/api/cross_references",
    description: "Fetch cross-references for a verse.",
    params: [
      { name: "verse", type: "text", default: "Genesis 1:1", placeholder: "e.g. Genesis 1:1, John 3:16" }
    ]
  },
  tradition_works: {
    route: "/api/tradition/works",
    description: "List all ingested tradition works (Didache, Council Canons, Augustine, Chrysostom).",
    params: []
  },
  tradition_passages: {
    route: "/api/tradition/passages",
    description: "Fetch passages for a specific tradition work by ID.",
    params: [
      { name: "work_id", type: "number", default: "1", placeholder: "e.g. 1, 2, 3, 4" }
    ]
  }
};

const host = "http://localhost:8090";
let activeEndpoint = "versions";

// Elements
const endpointBtns = document.querySelectorAll(".endpoint-btn");
const endpointDesc = document.getElementById("endpoint-description");
const inputsContainer = document.getElementById("inputs-container");
const urlPreview = document.getElementById("request-url-preview");
const paramForm = document.getElementById("param-form");
const responseCode = document.getElementById("response-code");
const responseStatus = document.getElementById("response-status");
const copyBtn = document.getElementById("copy-btn");

// Setup sidebar triggers
endpointBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    endpointBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    
    activeEndpoint = btn.getAttribute("data-endpoint");
    renderParams();
  });
});

// Render parameter inputs
function renderParams() {
  const spec = ENDPOINTS[activeEndpoint];
  endpointDesc.textContent = spec.description;
  inputsContainer.innerHTML = "";

  if (spec.params.length === 0) {
    inputsContainer.innerHTML = '<p style="font-size: 0.85rem; color: var(--text-secondary);">No parameters required.</p>';
  } else {
    spec.params.forEach(p => {
      const group = document.createElement("div");
      group.className = "form-group";
      
      const label = document.createElement("label");
      label.textContent = p.name;
      label.setAttribute("for", `input-${p.name}`);
      group.appendChild(label);

      if (p.type === "select") {
        const select = document.createElement("select");
        select.id = `input-${p.name}`;
        select.name = p.name;
        
        p.options.forEach(opt => {
          const option = document.createElement("option");
          option.value = opt;
          option.textContent = opt === "" ? "All Types" : opt;
          if (opt === p.default) option.selected = true;
          select.appendChild(option);
        });

        select.addEventListener("change", updateUrlPreview);
        group.appendChild(select);
      } else {
        const input = document.createElement("input");
        input.id = `input-${p.name}`;
        input.name = p.name;
        input.type = p.type;
        input.value = p.default;
        input.placeholder = p.placeholder;

        input.addEventListener("input", updateUrlPreview);
        group.appendChild(input);
      }

      inputsContainer.appendChild(group);
    });
  }

  updateUrlPreview();
}

// Update requested URL preview
function updateUrlPreview() {
  const spec = ENDPOINTS[activeEndpoint];
  let url = `${host}${spec.route}`;
  
  if (spec.params.length > 0) {
    const params = new URLSearchParams();
    spec.params.forEach(p => {
      const input = document.getElementById(`input-${p.name}`);
      if (input && input.value) {
        params.append(p.name, input.value);
      }
    });
    
    const queryStr = params.toString();
    if (queryStr) {
      url += `?${queryStr}`;
    }
  }

  urlPreview.textContent = url;
}

// Send Request Trigger
paramForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  
  const url = urlPreview.textContent;
  responseStatus.className = "status-badge status-none";
  responseStatus.textContent = "Loading...";
  responseCode.textContent = "Fetching response...";
  responseCode.className = "json-code empty";
  copyBtn.disabled = true;

  try {
    const startTime = performance.now();
    const response = await fetch(url);
    const endTime = performance.now();
    const timeTaken = Math.round(endTime - startTime);

    const data = await response.json();
    
    // Status color
    if (response.ok) {
      responseStatus.className = "status-badge status-success";
      responseStatus.textContent = `${response.status} OK (${timeTaken}ms)`;
      responseCode.className = "json-code";
      copyBtn.disabled = false;
    } else {
      responseStatus.className = "status-badge status-error";
      responseStatus.textContent = `${response.status} Error (${timeTaken}ms)`;
      responseCode.className = "json-code empty";
    }

    responseCode.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    responseStatus.className = "status-badge status-error";
    responseStatus.textContent = "Failed";
    responseCode.className = "json-code empty";
    responseCode.textContent = `Network Error: Could not connect to API server at ${host}.\nEnsure python scripts/python/api_server.py is running.`;
  }
});

// Copy to clipboard
copyBtn.addEventListener("click", () => {
  const code = responseCode.textContent;
  if (!code || copyBtn.disabled) return;

  navigator.clipboard.writeText(code).then(() => {
    const originalText = copyBtn.textContent;
    copyBtn.textContent = "Copied!";
    setTimeout(() => {
      copyBtn.textContent = originalText;
    }, 1500);
  });
});

// Start
renderParams();
