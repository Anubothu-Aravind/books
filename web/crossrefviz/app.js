// Books of the Bible list in order
const CANON_BOOKS = [
  "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
  "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah",
  "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
  "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
  "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
  "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians",
  "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
  "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
  "1 John", "2 John", "3 John", "Jude", "Revelation"
];

const NT_BOOKS = [
  "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians",
  "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
  "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
  "1 John", "2 John", "3 John", "Jude", "Revelation"
];

// Book name to folder mapping (same as in ingestion scripts)
const BOOK_FOLDERS = {
  "Genesis": "01_genesis", "Exodus": "02_exodus", "Leviticus": "03_leviticus",
  "Numbers": "04_numbers", "Deuteronomy": "05_deuteronomy", "Joshua": "06_joshua",
  "Judges": "07_judges", "Ruth": "08_ruth", "1 Samuel": "09_1samuel", "2 Samuel": "10_2samuel",
  "1 Kings": "11_1kings", "2 Kings": "12_2kings", "1 Chronicles": "13_1chronicles",
  "2 Chronicles": "14_2chronicles", "Ezra": "15_ezra", "Nehemiah": "16_nehemiah",
  "Esther": "17_esther", "Job": "18_job", "Psalms": "19_psalms", "Proverbs": "20_proverbs",
  "Ecclesiastes": "21_ecclesiastes", "Song of Solomon": "22_songofsolomon", "Isaiah": "23_isaiah",
  "Jeremiah": "24_jeremiah", "Lamentations": "25_lamentations", "Ezekiel": "26_ekeziel",
  "Daniel": "27_daniel", "Hosea": "28_hosea", "Joel": "29_joel", "Amos": "30_amos",
  "Obadiah": "31_obadiah", "Jonah": "32_jonah", "Micah": "33_micah", "Nahum": "34_nahum",
  "Habakkuk": "35_habakkuk", "Zephaniah": "36_zephaniah", "Haggai": "37_haggai",
  "Zechariah": "38_zechariah", "Malachi": "39_malachi",
  "Matthew": "01_matthew", "Mark": "02_mark", "Luke": "03_luke", "John": "04_john",
  "Acts": "05_acts", "Romans": "06_romans", "1 Corinthians": "07_1corinthians",
  "2 Corinthians": "08_2corinthians", "Galatians": "09_galatians", "Ephesians": "10_ephesians",
  "Philippians": "11_philippians", "Colossians": "12_colossians", "1 Thessalonians": "13_1thessalonians",
  "2 Thessalonians": "14_2thessalonians", "1 Timothy": "15_1timothy", "2 Timothy": "16_2timothy",
  "Titus": "17_titus", "Philemon": "18_philemon", "Hebrews": "19_hebrews", "James": "20_james",
  "1 Peter": "21_1peter", "2 Peter": "22_2peter", "1 John": "23_1john", "2 John": "24_2john",
  "3 John": "25_3john", "Jude": "26_jude", "Revelation": "27_revelation"
};

// Global variables
let matrixData = [];
let crossRefsCache = null;
let selectedCell = null; // {row, col}
let maxRefValue = 1;

// Elements
const canvas = document.getElementById("heatmapCanvas");
const ctx = canvas.getContext("2d");
const tooltip = document.getElementById("tooltip");
const selectionInfo = document.getElementById("selection-info");
const bookInfoSummary = document.querySelector(".book-info-summary");
const sourceBookVal = document.getElementById("source-book-val");
const targetBookVal = document.getElementById("target-book-val");
const connectionsCountVal = document.getElementById("connections-count-val");
const emptyState = document.getElementById("empty-state");
const loadingIndicator = document.getElementById("loading-indicator");
const versesList = document.getElementById("verses-list");

// Heatmap settings
const labelOffsetLeft = 120;
const labelOffsetBottom = 120;
let gridWidth, gridHeight;
let cellSize;

// Initialize app
async function init() {
  resizeCanvas();
  window.addEventListener("resize", () => {
    resizeCanvas();
    drawHeatmap();
  });

  try {
    await loadMatrix();
    drawHeatmap();
    setupCanvasListeners();
  } catch (error) {
    console.error("Failed to initialize visualization:", error);
  }
}

function resizeCanvas() {
  const container = canvas.parentElement;
  const size = Math.min(container.clientWidth, container.clientHeight, 850);
  canvas.width = size;
  canvas.height = size;
  
  gridWidth = canvas.width - labelOffsetLeft - 20;
  gridHeight = canvas.height - labelOffsetBottom - 20;
  cellSize = gridWidth / 66;
}

// Load 66x66 book cross references matrix from CSV
async function loadMatrix() {
  const response = await fetch("../../cross_references/book_matrix.csv");
  if (!response.ok) throw new Error("Could not fetch book_matrix.csv");
  const text = await response.text();
  
  const rows = text.split("\n").map(r => r.split(","));
  // Row 0 is header. Rows 1 to 66 contain the data.
  matrixData = [];
  maxRefValue = 1;

  for (let i = 1; i <= 66; i++) {
    if (!rows[i] || rows[i].length < 67) continue;
    const rowBook = rows[i][0].trim();
    const rowCounts = [];
    for (let j = 1; j <= 66; j++) {
      const count = parseInt(rows[i][j]) || 0;
      rowCounts.push(count);
      if (count > maxRefValue) {
        maxRefValue = count;
      }
    }
    matrixData.push({ book: rowBook, counts: rowCounts });
  }
}

// Draw the 66x66 matrix
function drawHeatmap() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // Background
  ctx.fillStyle = "#0b0f19";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (matrixData.length === 0) return;

  // Draw cells
  for (let r = 0; r < 66; r++) {
    for (let c = 0; c < 66; c++) {
      const count = matrixData[r].counts[c];
      
      // Determine color intensity based on log-scale value
      let intensity = 0;
      if (count > 0) {
        // Use logarithmic scaling to make low values visible
        intensity = Math.log(count) / Math.log(maxRefValue);
      }

      // Base color logic: dark dark blue/black -> indigo -> bright cyan
      ctx.fillStyle = getCellColor(intensity);
      
      const x = labelOffsetLeft + c * cellSize;
      const y = r * cellSize;
      
      ctx.fillRect(x, y, cellSize - 1, cellSize - 1);

      // Highlight selected cell
      if (selectedCell && selectedCell.row === r && selectedCell.col === c) {
        ctx.strokeStyle = "#06b6d4";
        ctx.lineWidth = 2;
        ctx.strokeRect(x - 0.5, y - 0.5, cellSize, cellSize);
      }
    }
  }

  // Draw Y-axis labels (Source Books)
  ctx.fillStyle = "#9ca3af";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (let r = 0; r < 66; r++) {
    const book = CANON_BOOKS[r];
    const y = r * cellSize + cellSize / 2;
    ctx.fillText(book, labelOffsetLeft - 10, y);
  }

  // Draw X-axis labels (Target Books)
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  for (let c = 0; c < 66; c++) {
    const book = CANON_BOOKS[c];
    const x = labelOffsetLeft + c * cellSize + cellSize / 2;
    const y = gridHeight + 10;
    
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(Math.PI / 2);
    ctx.fillText(book, 0, 0);
    ctx.restore();
  }
}

// Convert intensity (0 to 1) into a beautiful glowing neon gradient
function getCellColor(intensity) {
  if (intensity === 0) return "#111827"; // Dark dark gray

  // Interpolate between deep purple (#311082) and bright cyan (#06b6d4)
  const r = Math.floor(49 + intensity * (6 - 49));
  const g = Math.floor(16 + intensity * (182 - 16));
  const b = Math.floor(130 + intensity * (212 - 130));
  return `rgb(${r}, ${g}, ${b})`;
}

// Interactive hover and click handlers
function setupCanvasListeners() {
  canvas.addEventListener("mousemove", handleMouseMove);
  canvas.addEventListener("mouseout", () => {
    tooltip.style.opacity = 0;
  });
  canvas.addEventListener("click", handleMouseClick);
}

function getCellFromCoords(clientX, clientY) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  
  const canvasX = (clientX - rect.left) * scaleX;
  const canvasY = (clientY - rect.top) * scaleY;

  if (canvasX >= labelOffsetLeft && canvasX < labelOffsetLeft + gridWidth &&
      canvasY >= 0 && canvasY < gridHeight) {
    const col = Math.floor((canvasX - labelOffsetLeft) / cellSize);
    const row = Math.floor(canvasY / cellSize);
    return { row, col };
  }
  return null;
}

function handleMouseMove(e) {
  const cell = getCellFromCoords(e.clientX, e.clientY);
  if (cell) {
    const sourceBook = CANON_BOOKS[cell.row];
    const targetBook = CANON_BOOKS[cell.col];
    const count = matrixData[cell.row].counts[cell.col];

    tooltip.innerHTML = `
      <strong style="color: #06b6d4">${sourceBook}</strong> ➔ 
      <strong style="color: #8b5cf6">${targetBook}</strong><br>
      <strong>${count.toLocaleString()}</strong> connections
    `;
    tooltip.style.left = `${e.pageX + 15}px`;
    tooltip.style.top = `${e.pageY + 15}px`;
    tooltip.style.opacity = 1;
  } else {
    tooltip.style.opacity = 0;
  }
}

async function handleMouseClick(e) {
  const cell = getCellFromCoords(e.clientX, e.clientY);
  if (!cell) return;

  selectedCell = cell;
  drawHeatmap();

  const sourceBook = CANON_BOOKS[cell.row];
  const targetBook = CANON_BOOKS[cell.col];
  const count = matrixData[cell.row].counts[cell.col];

  // Update summary info
  selectionInfo.style.display = "none";
  bookInfoSummary.style.display = "grid";
  sourceBookVal.textContent = sourceBook;
  targetBookVal.textContent = targetBook;
  connectionsCountVal.textContent = count.toLocaleString();

  if (count === 0) {
    emptyState.style.display = "flex";
    versesList.style.display = "none";
    versesList.innerHTML = "";
    return;
  }

  // Show loading indicator
  emptyState.style.display = "none";
  loadingIndicator.style.display = "flex";
  versesList.style.display = "none";
  versesList.innerHTML = "";

  try {
    const xreflist = await loadDetailConnections(sourceBook, targetBook);
    renderVerseConnections(xreflist);
  } catch (error) {
    console.error("Error loading connection details:", error);
    loadingIndicator.style.display = "none";
    emptyState.style.display = "flex";
    emptyState.querySelector("p").textContent = "Failed to load detailed connection data.";
  }
}

// Lazy-load the full cross_references map (15MB) once
async function getCrossRefs() {
  if (crossRefsCache) return crossRefsCache;
  const response = await fetch("../../cross_references/cross_references.json");
  if (!response.ok) throw new Error("Could not fetch cross_references.json");
  crossRefsCache = await response.json();
  return crossRefsCache;
}

// Get connections matching the selected source/target book pair
async function loadDetailConnections(sourceBook, targetBook) {
  const refs = await getCrossRefs();
  const results = [];

  for (const [sourceVerse, targets] of Object.entries(refs)) {
    if (!sourceVerse.startsWith(sourceBook)) continue;
    
    // Validate exact book match
    const srcBookPart = sourceVerse.substring(0, sourceVerse.lastIndexOf(" "));
    if (srcBookPart !== sourceBook) continue;

    for (const target of targets) {
      const destVerse = target.target;
      if (!destVerse.startsWith(targetBook)) continue;
      
      const destBookPart = destVerse.substring(0, destVerse.lastIndexOf(" "));
      if (destBookPart !== targetBook) continue;

      results.push({
        source: sourceVerse,
        target: destVerse,
        votes: target.votes
      });
    }
  }

  // Sort by connection strength/votes
  return results.sort((a, b) => b.votes - a.votes).slice(0, 100); // Limit to top 100 details for performance
}

// Renders the list of connections and fetches the verse texts dynamically
async function renderVerseConnections(connections) {
  loadingIndicator.style.display = "none";
  if (connections.length === 0) {
    emptyState.style.display = "flex";
    return;
  }

  versesList.style.display = "flex";
  versesList.innerHTML = "";

  for (const conn of connections) {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="ref-row">
        <span class="ref-source">${conn.source}</span>
        <span class="ref-arrow">➔</span>
        <span class="ref-target">${conn.target}</span>
        <span class="votes-badge">${conn.votes} votes</span>
      </div>
      <div class="verse-text-container">
        <div class="verse-item source-text">
          <div class="verse-item-label">${conn.source} (KJV)</div>
          <div class="verse-content" data-ref="${conn.source}">Loading text...</div>
        </div>
        <div class="verse-item target-text">
          <div class="verse-item-label">${conn.target} (KJV)</div>
          <div class="verse-content" data-ref="${conn.target}">Loading text...</div>
        </div>
      </div>
    `;
    versesList.appendChild(li);

    // Fetch verse texts asynchronously
    fetchVerseText(conn.source, li.querySelector(`.verse-content[data-ref="${conn.source}"]`));
    fetchVerseText(conn.target, li.querySelector(`.verse-content[data-ref="${conn.target}"]`));
  }
}

// Cache for loaded chapter text files to avoid duplicate requests
const chapterCache = {};

async function fetchVerseText(verseRef, element) {
  // Parse ref: e.g. "Genesis 1:1" or "1 John 1:1"
  const spaceIdx = verseRef.lastIndexOf(" ");
  const bookName = verseRef.substring(0, spaceIdx);
  const colonIdx = verseRef.indexOf(":", spaceIdx);
  const chapter = parseInt(verseRef.substring(spaceIdx + 1, colonIdx));
  const verse = parseInt(verseRef.substring(colonIdx + 1));

  const bookFolder = BOOK_FOLDERS[bookName];
  if (!bookFolder) {
    element.textContent = "[Unknown book folder]";
    return;
  }

  const testament = NT_BOOKS.includes(bookName) ? "nt" : "ot";
  const path = `../../bible/english/kjv/${testament}/${bookFolder}/chapter_${String(chapter).padStart(3, "0")}.txt`;

  try {
    let lines;
    if (chapterCache[path]) {
      lines = chapterCache[path];
    } else {
      const response = await fetch(path);
      if (!response.ok) {
        element.textContent = "[Verse unavailable]";
        return;
      }
      const text = await response.text();
      lines = text.split("\n");
      chapterCache[path] = lines;
    }

    // Find line with "Verse V]"
    let foundText = null;
    const matchLabel = `Verse ${verse}]`;
    for (const line of lines) {
      if (line.includes(matchLabel)) {
        const bracketIdx = line.indexOf("]");
        foundText = line.substring(bracketIdx + 1).trim();
        break;
      }
    }

    if (foundText) {
      element.textContent = foundText;
    } else {
      element.textContent = "[Verse not found]";
    }
  } catch (error) {
    element.textContent = "[Failed to load text]";
  }
}

// Start application
init();
