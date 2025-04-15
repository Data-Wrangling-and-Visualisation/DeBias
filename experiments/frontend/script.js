// --- Global Variables ---
let allArticlesData = [];
let processedDataByDate = new Map(); // Stores {nodes, links} for each date
let availableDates = [];
let currentGraphData = { nodes: [], links: [] }; // Holds data currently displayed
let svg, simulation, g, link, nodeGroup, label, tooltip, edgeInfo, legend; // D3 selections
let maxPopularity = 1; // Max keyword count across all dates for slider range

// --- Constants ---
const classCategories = [
    "politics", "economy", "business", "technology",
    "health", "science", "sports", "entertainment", "education", "environment"
];
const classColors = {
    "politics": "#FF5733", "economy": "#33FF57", "business": "#3357FF",
    "technology": "#F033FF", "health": "#33FFF0", "science": "#FFF033",
    "sports": "#FF33A8", "entertainment": "#A833FF", "education": "#FF8C33",
    "environment": "#33FF8C"
};
const defaultColor = "#999999";

// --- DOM Elements ---
// Use d3.select for consistency, although document.getElementById etc. would also work
const dateSelect = d3.select("#date-select");
const categoryFiltersDiv = d3.select("#category-filters");
const popularitySlider = d3.select("#popularity-slider");
const popularityValueSpan = d3.select("#popularity-value");
const popularityMaxNodesInput = d3.select("#popularity-max-nodes");
const loadingDiv = d3.select(".loading");
const noDataMessage = d3.select("#no-data-message");
const graphContainer = d3.select("#graph-container"); // Get graph container
const graphDiv = d3.select("#graph"); // Get the div where SVG will be placed
const selectAllCatsButton = d3.select("#select-all-cats");
const deselectAllCatsButton = d3.select("#deselect-all-cats");
const resetFiltersButton = d3.select("#reset-filters");

// --- Initial Setup ---
// Wait for the DOM to be fully loaded before setting up SVG and legend
document.addEventListener('DOMContentLoaded', () => {
    setupGraphSVG();
    setupLegend(); // Setup static legend parts

    // --- Load Data ---
    fetch('parsed_news.json') // Make sure this path is correct relative to index.html
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(rawData => {
            allArticlesData = rawData;
            preprocessData(allArticlesData);
            populateControls(); // Now safe to populate controls that depend on data
            loadingDiv.style('display', 'none'); // Hide loading indicator
            // Trigger initial graph render for the first available date
            if (availableDates.length > 0) {
                dateSelect.property('value', availableDates[0]); // Select first date
                updateGraph(); // Render initial graph
            } else {
                 noDataMessage.style('display', 'block').text("No articles found in the data.");
            }
        })
        .catch(error => {
            console.error('Error loading or processing the data:', error);
            loadingDiv.text(`Error loading data: ${error.message}. Check console.`);
            noDataMessage.style('display', 'block').text("Failed to load or process news data.");
        });
});


// --- Data Pre-processing ---
function preprocessData(articles) {
    // Group articles by the DATE PART ONLY (YYYY-MM-DD)
    const articlesByDate = d3.group(articles, d => {
        if (d.date && typeof d.date === 'string' && d.date.length >= 10) {
            // Extract the first 10 characters which represent YYYY-MM-DD
            return d.date.substring(0, 10);
        }
        return 'unknown_date'; // Handle cases where date is missing or invalid
    });

    // Get sorted list of unique YYYY-MM-DD dates
    availableDates = Array.from(articlesByDate.keys())
                        .filter(date => date !== 'unknown_date') // Remove the placeholder if it exists
                        .sort(); // Sort dates chronologically

    let globalMaxPop = 0;

    availableDates.forEach(date => {
        const dailyArticles = articlesByDate.get(date);
        if (dailyArticles) { // Ensure there are articles for this date key
            const graphData = processSingleDateData(dailyArticles);
            processedDataByDate.set(date, graphData);

            // Find the max popularity for this date
            const dateMaxPop = d3.max(graphData.nodes, d => d.count) || 0;
            if (dateMaxPop > globalMaxPop) {
                globalMaxPop = dateMaxPop;
            }
        }
    });

    maxPopularity = globalMaxPop > 1 ? globalMaxPop : 10; // Set slider max (min 10)
    popularitySlider.attr("max", maxPopularity);

    // Adjust initial slider value if needed
     const currentSliderVal = parseInt(popularitySlider.property("value"));
    if (currentSliderVal > maxPopularity) {
         const newVal = Math.min(5, maxPopularity); // Set a reasonable default if max is low
         popularitySlider.property("value", newVal);
         popularityValueSpan.text(newVal);
    } else if (maxPopularity <= 1) {
         popularitySlider.property("value", 1);
         popularityValueSpan.text(1);
    } else {
        // Update display if initial value is valid but different from default
        popularityValueSpan.text(currentSliderVal);
    }
}


// Process data for a single date (similar to original processData)
function processSingleDateData(articles) {
    const nodes = new Map();
    const links = new Map(); // Use map for easier link aggregation

    articles.forEach(article => {
        const keywords = Array.isArray(article.keywords) ? article.keywords : [];

        keywords.forEach(keyword => {
            // Basic check for empty/null keywords
            if (!keyword || typeof keyword !== 'string' || keyword.trim() === '') return;
            const trimmedKeyword = keyword.trim(); // Use trimmed keyword

            if (!nodes.has(trimmedKeyword)) {
                const isClass = classCategories.includes(trimmedKeyword.toLowerCase());
                nodes.set(trimmedKeyword, {
                    id: trimmedKeyword,
                    articles: [article],
                    count: 1,
                    isClass: isClass,
                    class: isClass ? trimmedKeyword.toLowerCase() : null,
                    categoryConnections: {} // Calculate later
                });
            } else {
                const node = nodes.get(trimmedKeyword);
                node.articles.push(article);
                node.count += 1;
            }
        });

        // Create links (use trimmed keywords)
        const articleKeywords = keywords.map(k => k?.trim()).filter(Boolean); // Trimmed and filtered list
        for (let i = 0; i < articleKeywords.length; i++) {
            for (let j = i + 1; j < articleKeywords.length; j++) {
                const source = articleKeywords[i];
                const target = articleKeywords[j];
                 if (source === target) continue; // Don't link a keyword to itself

                // Create a unique key for the link (order independent)
                const linkKey = [source, target].sort().join('||');

                if (links.has(linkKey)) {
                    const link = links.get(linkKey);
                    link.value += 1;
                    if (!link.articles.some(a => a.url === article.url)) { // Avoid duplicate article refs if possible
                         link.articles.push(article);
                    }
                } else {
                    links.set(linkKey, {
                        source: source, // Store the actual keyword ID
                        target: target,
                        value: 1,
                        articles: [article]
                    });
                }
            }
        }
    });

    // Calculate category connections for non-class nodes
    const finalLinks = Array.from(links.values());
    const finalNodes = Array.from(nodes.values());

    finalNodes.forEach(node => {
         if (!node.isClass) {
            node.categoryConnections = {}; // Initialize here
            finalLinks.forEach(link => {
                let otherNodeId = null;
                // Check source/target which might be objects or strings depending on D3 version/usage
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;

                if (sourceId === node.id) otherNodeId = targetId;
                else if (targetId === node.id) otherNodeId = sourceId;

                if (otherNodeId) {
                     const otherNode = nodes.get(otherNodeId); // Use the original map for lookup
                     if (otherNode && otherNode.isClass) {
                         const category = otherNode.class;
                         node.categoryConnections[category] = (node.categoryConnections[category] || 0) + link.value;
                     }
                 }
            });

             // Calculate primary class and percentages
            const connections = node.categoryConnections;
            if (Object.keys(connections).length > 0) {
                node.relatedClasses = Object.keys(connections);
                // Find the class with the highest connection count
                node.primaryClass = Object.entries(connections)
                    .reduce((a, b) => a[1] > b[1] ? a : b)[0]; // Find max entry based on value

                const totalConnections = Object.values(connections).reduce((a, b) => a + b, 0);
                node.categoryPercentages = {};
                if (totalConnections > 0) {
                     Object.entries(connections).forEach(([category, count]) => {
                        node.categoryPercentages[category] = count / totalConnections;
                    });
                }
            } else {
                node.primaryClass = null; // No connections to categories
                node.relatedClasses = [];
                node.categoryPercentages = {};
            }
        } else {
            // For class nodes, set primaryClass to itself for easier filtering
             node.primaryClass = node.class;
             node.relatedClasses = [node.class];
             node.categoryPercentages = {[node.class]: 1}; // Represents 100% itself
        }
    });

    return {
        nodes: finalNodes,
        links: finalLinks
    };
}

// --- UI Control Setup ---
function populateControls() {
    // Date Selector
    dateSelect.selectAll('option')
        .data(availableDates)
        .join('option') // Use join for potential updates later
        .attr('value', d => d)
        .text(d => d);

    // Category Filters
    categoryFiltersDiv.selectAll('.category-filter-item')
        .data(classCategories)
        .join('div') // Use join
        .attr('class', 'category-filter-item')
        .html(d => `
            <label>
                <input type="checkbox" class="category-checkbox" value="${d}" checked>
                ${d.charAt(0).toUpperCase() + d.slice(1)}
            </label>
        `);

    // Add event listeners AFTER elements are created
    dateSelect.on('change', updateGraph);
    categoryFiltersDiv.selectAll('.category-checkbox').on('change', updateGraph);
    popularitySlider.on('input', () => {
        popularityValueSpan.text(popularitySlider.property('value'));
        // No need to call updateGraph here, use 'change' event for less frequent updates
    });
    popularitySlider.on('change', updateGraph); // Update graph when slider value is finalized

    popularityMaxNodesInput.on('change', updateGraph);

    selectAllCatsButton.on('click', () => {
        categoryFiltersDiv.selectAll('.category-checkbox').property('checked', true);
        updateGraph();
    });
    deselectAllCatsButton.on('click', () => {
        categoryFiltersDiv.selectAll('.category-checkbox').property('checked', false);
        updateGraph();
    });
    resetFiltersButton.on('click', () => {
        if (availableDates.length > 0) {
            dateSelect.property('value', availableDates[0]);
        }
        categoryFiltersDiv.selectAll('.category-checkbox').property('checked', true);
        popularitySlider.property("value", 1);
        popularityValueSpan.text(1);
        popularityMaxNodesInput.property("value", 150);
        updateGraph();
    });
}


// --- Filtering Logic ---
function filterData(originalData) {
    const selectedCategories = categoryFiltersDiv.selectAll('.category-checkbox:checked').nodes().map(cb => cb.value);
    const minPopularity = parseInt(popularitySlider.property('value'));
    const maxNodes = parseInt(popularityMaxNodesInput.property('value'));

    if (!originalData || !originalData.nodes) {
        return { nodes: [], links: [] }; // Return empty if no original data
    }

    let filteredNodes = originalData.nodes.filter(node => {
        // Popularity Filter
        if (node.count < minPopularity) {
            return false;
        }

        // Category Filter
         // If NO categories are selected, only show nodes that have NO category affiliation at all?
         // Or show all nodes respecting only popularity? Let's show nodes matching popularity if no cats selected.
         if (selectedCategories.length === 0) {
             return true; // Show all nodes that pass popularity filter if no category is selected
         }

         // If categories ARE selected:
        if (node.isClass) {
            // Keep class node only if its category is selected
            return selectedCategories.includes(node.class);
         } else {
             // Keep non-class node if its primary class is selected OR any of its related classes are selected
             return selectedCategories.includes(node.primaryClass) ||
                   (node.relatedClasses && node.relatedClasses.some(cat => selectedCategories.includes(cat)));
         }
         // This line shouldn't be reached due to the logic above, but as a fallback:
         // return false;
    });

     // Max Nodes Limit (applied after other filters, prioritizing higher count)
     if (filteredNodes.length > maxNodes) {
        // Sort by popularity descending, then alphabetically for tie-breaking
        filteredNodes.sort((a, b) => {
            const countDiff = b.count - a.count;
            if (countDiff !== 0) return countDiff;
            return a.id.localeCompare(b.id);
        });
        filteredNodes = filteredNodes.slice(0, maxNodes);
    }

    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));

    // Filter Links: Keep link only if both source and target nodes are in the filtered set
    const filteredLinks = originalData.links.filter(link => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
         return filteredNodeIds.has(sourceId) && filteredNodeIds.has(targetId);
    });

    return { nodes: filteredNodes, links: filteredLinks };
}

// --- D3 Graph Rendering ---
function setupGraphSVG() {
    // Get dimensions from container AFTER DOM is ready
    const width = graphContainer.node().getBoundingClientRect().width;
    const height = graphContainer.node().getBoundingClientRect().height;

    svg = graphDiv // Select the specific div for the SVG
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height]) // Improves responsiveness
        .attr("style", "max-width: 100%; height: auto; height: intrinsic;") // More CSS for responsiveness
        .call(d3.zoom().scaleExtent([0.1, 8]).on("zoom", (event) => {
            if (g) g.attr("transform", event.transform);
        }));

    // Append the main group 'g' element where graph elements will live
     g = svg.append("g");

    // Select tooltip and edge info divs (already exist in HTML)
    tooltip = d3.select(".tooltip");
    edgeInfo = d3.select(".edge-info");

     // Add background click handler to reset highlights
     svg.on("click", function(event) {
         // Prevent reset if click is on a node/link (handled by their specific handlers)
         if (event.target.closest(".node-group") || event.target.closest(".link")) {
             return;
         }
         resetHighlights(currentGraphData); // Pass current data to reset colors correctly
     });

     // Handle window resizing
    window.addEventListener('resize', () => {
        const newWidth = graphContainer.node().getBoundingClientRect().width;
        const newHeight = graphContainer.node().getBoundingClientRect().height;
        svg.attr("width", newWidth)
           .attr("height", newHeight)
           .attr("viewBox", [0, 0, newWidth, newHeight]);
        // Optionally recenter or restart simulation on resize
        if (simulation) {
            simulation.force("center", d3.forceCenter(newWidth / 2, newHeight / 2)).alpha(0.1).restart();
        }
    });
}

function setupLegend() {
    legend = d3.select(".legend");
    legend.html(""); // Clear previous legend content

    legend.append("h3").text("Categories");
     Object.entries(classColors).forEach(([category, color]) => {
        const item = legend.append("div").attr("class", "legend-item");
        item.append("div")
            .attr("class", "legend-color")
            .style("background-color", color);
        item.append("span").text(category.charAt(0).toUpperCase() + category.slice(1));
    });

     legend.append("h3").text("Edge Thickness");
    legend.append("p").text("Represents co-occurrence count").style("font-size", "10px");

     legend.append("h3").text("Node Visualization");
    legend.append("p").html(`
        Size: Popularity<br>
        Color/Pie: Category affinity<br>
        <b>Bold</b> Label: Category Node
        `).style("font-size", "10px");
}

function updateGraph() {
     const selectedDate = dateSelect.property('value');
     const originalData = processedDataByDate.get(selectedDate);

     if (!originalData || !originalData.nodes) {
         clearGraph();
         console.warn(`No preprocessed data found for date: ${selectedDate}`);
         noDataMessage.style('display', 'block').text(`No data available for ${selectedDate}.`);
         currentGraphData = { nodes: [], links: [] }; // Reset current data
         return;
     }

     currentGraphData = filterData(JSON.parse(JSON.stringify(originalData))); // Filter a deep copy

     if (currentGraphData.nodes.length === 0) {
          clearGraph();
          noDataMessage.style('display', 'block').text(`No data matches the current filters for ${selectedDate}.`);
          return;
     }

     noDataMessage.style('display', 'none');
     renderGraph(currentGraphData);
 }

function clearGraph() {
    if (simulation) {
        simulation.stop(); // Stop the simulation
        simulation = null; // Release simulation object
    }
    if (g) {
        g.selectAll("*").remove(); // Clear contents of the main group
    } else if (svg) {
        // If g wasn't created or found, ensure svg is clear
        svg.selectAll("g").remove();
        g = svg.append("g"); // Recreate the main group if needed
    }
    // No need to hide noDataMessage here, renderGraph or updateGraph will manage it
}

function renderGraph(data) {
    clearGraph(); // Clear previous graph elements and stop simulation

    if (!data || !data.nodes || data.nodes.length === 0) {
        console.log("No data to render.");
        noDataMessage.style('display', 'block').text("No data to display with current filters.");
        return;
    }

    const width = graphContainer.node().getBoundingClientRect().width;
    const height = graphContainer.node().getBoundingClientRect().height;

    // Ensure 'g' exists
    if (!g) {
        g = svg.append("g");
    }

    // --- Simulation Setup (Re-initialize for new data) ---
    simulation = d3.forceSimulation(data.nodes)
        .force("charge", d3.forceManyBody().strength(-150 - data.nodes.length)) // Adjust strength based on node count
        .force("link", d3.forceLink(data.links)
             .id(d => d.id)
             .distance(d => 70 + 60 / (Math.sqrt(d.value) || 1)) // Adjust link distance based on value
             .strength(d => 0.4 + 0.6 / (d.value || 1)) // Stronger links for higher value? Experiment.
        )
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(d => getNodeRadius(d) + 4).strength(0.7)) // Collision radius
        .on("tick", ticked); // Define tick handler separately


    // --- Create Links ---
    link = g.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(data.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`) // Key function for object constancy
        .join("line") // Use join for enter/update/exit
        .attr("class", "link")
        .attr("stroke-width", d => Math.max(1, Math.sqrt(d.value) * 1.2)) // Link width
        .style("stroke", d => getLinkColor(d, data.nodes))
        .style("stroke-opacity", 0.6);


    // --- Create Node Groups ---
    nodeGroup = g.append("g")
        .attr("class", "nodes")
        .selectAll("g.node-group")
        .data(data.nodes, d => d.id) // Key function for object constancy
        .join("g") // Use join
        .attr("class", "node-group")
        .call(d3.drag() // Apply drag behavior
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    // Pie chart setup (can be defined once outside)
    const pie = d3.pie().sort(null).value(d => d.value);
    const arc = d3.arc().innerRadius(0);

    // Add node visuals (circles or pies)
    nodeGroup.each(function(d) {
        const group = d3.select(this);
        // group.selectAll("*").remove(); // Join should handle removal, but clear just in case

        const radius = getNodeRadius(d);
        arc.outerRadius(radius); // Update arc generator radius

        // Determine if node should be simple circle or pie
        const showPie = !d.isClass && d.categoryPercentages && Object.keys(d.categoryPercentages).length > 1;

        if (!showPie) {
             group.append("circle")
                .attr("r", radius)
                .attr("fill", getNodeColor(d))
                .attr("stroke", d.isClass ? "#333" : getNodeColor(d)) // Outline class nodes
                .attr("stroke-width", d.isClass ? 1.5 : 0.5);
        } else {
            const pieData = Object.entries(d.categoryPercentages)
                                .map(([key, value]) => ({ key, value }))
                                .filter(entry => entry.value > 0); // Filter out 0% slices

            if (pieData.length > 0) {
                const pieSlices = pie(pieData);
                group.selectAll(".pie-slice")
                    .data(pieSlices)
                    .join("path") // Use join for slices
                    .attr("class", "pie-slice")
                    .attr("d", arc)
                    .attr("fill", slice => classColors[slice.data.key] || defaultColor)
                    .attr("stroke", "#fff")
                    .attr("stroke-width", 0.5);
            } else {
                // Fallback to simple circle if pie data is empty after filtering
                 group.append("circle")
                    .attr("r", radius)
                    .attr("fill", getNodeColor(d))
                    .attr("stroke", d.isClass ? "#333" : getNodeColor(d))
                    .attr("stroke-width", d.isClass ? 1.5 : 0.5);
            }
        }
    });

     // --- Add Labels ---
    label = g.append("g")
        .attr("class", "labels")
        .selectAll("text")
        .data(data.nodes, d => d.id) // Key function
        .join("text") // Use join
        .attr("class", "node-label")
        .text(d => d.id)
        .attr("font-size", d => d.isClass ? 11 : Math.min(12, 6 + Math.sqrt(d.count))) // Adjust label size
        .attr("font-weight", d => d.isClass ? "bold" : "normal")
        .attr("dx", d => getNodeRadius(d) + 4) // Position relative to node radius
        .attr("dy", ".35em")
        .style("fill", "#333")
        .style("pointer-events", "none") // Prevent labels interfering with node events
        .style("text-shadow", "0 0 2px white, 0 0 2px white"); // Basic text shadow for readability


    // --- Setup Interactions ---
    setupNodeInteractions(data);
    setupLinkInteractions(data);


    // --- Simulation Tick Handler ---
    function ticked() {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        nodeGroup
            .attr("transform", d => `translate(${d.x},${d.y})`);

        // Labels are part of the 'labels' group, position them directly
         label
            .attr("x", d => d.x)
            .attr("y", d => d.y);
    }

    // Restart simulation with some alpha
    simulation.alpha(1).restart(); // Higher alpha initially
}


// --- Helper Functions ---
function getNodeRadius(d) {
    const baseSize = d.isClass ? 7 : 4;
    // Scale radius with square root of count, apply caps
    return Math.max(baseSize, Math.min(35, baseSize + Math.sqrt(d.count) * 2));
}

function getNodeColor(d) {
    if (d.isClass) {
         return classColors[d.class] || defaultColor;
     } else if (d.primaryClass && (!d.categoryPercentages || Object.keys(d.categoryPercentages).length <= 1)) {
         // Simple node or only one category connection - use primary class color with opacity
         return (classColors[d.primaryClass] || defaultColor) + "E6"; // E6 = 90% opacity
     } else if (!d.primaryClass && (!d.relatedClasses || d.relatedClasses.length === 0)) {
          // Node with no category connections at all
          return defaultColor + "B3"; // B3 = 70% opacity
     }
     // If it's a pie chart node, the color is handled by the pie slices.
     // Return a base color (e.g., light gray) in case pie slices don't cover fully, or transparent.
     return "#f0f0f0"; // Light gray base for pie nodes (mostly covered)
}

function getLinkColor(linkData, nodes) {
    const sourceNode = nodes.find(n => n.id === (linkData.source.id || linkData.source));
    const targetNode = nodes.find(n => n.id === (linkData.target.id || linkData.target));

    if (!sourceNode || !targetNode) return "#bbb"; // Fallback grey

    if (sourceNode.isClass && targetNode.isClass) {
        return blendColors(classColors[sourceNode.class], classColors[targetNode.class]) || "#aaa";
    } else if (sourceNode.isClass) {
        return (classColors[sourceNode.class] || "#bbb") + "99"; // 60% opacity
    } else if (targetNode.isClass) {
        return (classColors[targetNode.class] || "#bbb") + "99";
    } else if (sourceNode.primaryClass && targetNode.primaryClass && sourceNode.primaryClass === targetNode.primaryClass) {
        return (classColors[sourceNode.primaryClass] || "#bbb") + "73"; // 45% opacity
    } else if (sourceNode.primaryClass && targetNode.primaryClass) {
          // Blend between different primary classes? Or grey? Let's use lighter grey.
          return "#ccc"; // Lighter grey for mixed non-class links
     }

     return "#ddd"; // Default link color (e.g., between two nodes with no category affinity)
 }

// Function to blend two hex colors
function blendColors(color1, color2) {
     const hexToRgb = hex => {
        if (!hex || hex.length < 7 || !hex.startsWith('#')) return null; // Basic validation
        const bigint = parseInt(hex.slice(1), 16);
        const r = (bigint >> 16) & 255;
        const g = (bigint >> 8) & 255;
        const b = bigint & 255;
        return [r, g, b];
    };
    const rgbToHex = (r, g, b) => "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();

    const rgb1 = hexToRgb(color1);
    const rgb2 = hexToRgb(color2);

    if (!rgb1 || !rgb2) return null; // Return null if color conversion failed

    const blended = [ Math.round((rgb1[0] + rgb2[0]) / 2), Math.round((rgb1[1] + rgb2[1]) / 2), Math.round((rgb1[2] + rgb2[2]) / 2) ];
    return rgbToHex(...blended);
}

// --- Drag Functions ---
function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart(); // Heat up simulation
    d.fx = d.x; // Fix x position
    d.fy = d.y; // Fix y position
     d3.select(this).raise(); // Bring dragged node to front
}

function dragged(event, d) {
    d.fx = event.x; // Update fixed x position
    d.fy = event.y; // Update fixed y position
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0); // Cool down simulation
    // Keep node fixed after drag:
    // d.fx = d.x;
    // d.fy = d.y;
    // Or release it (allow simulation to position it again):
    d.fx = null;
    d.fy = null;
}

// --- Interaction Handlers ---
function setupNodeInteractions(data) {
    if (!nodeGroup || !link || !tooltip || !data || !data.nodes) return;

    nodeGroup.on("mouseover", function(event, d) {
        const nodeElement = d3.select(this);
        nodeElement.raise(); // Bring node to front visually

        // Highlight node and its label slightly
        nodeElement.select('circle, path').attr('stroke', '#333').attr('stroke-width', 2);
        label.filter(l => l.id === d.id).attr('font-weight', 'bold'); //.style('fill', 'black');


        // Highlight connected links and nodes
        const connectedNodeIds = new Set([d.id]);
        link.style("stroke-opacity", l => {
            const sourceId = l.source.id || l.source;
            const targetId = l.target.id || l.target;
            const isConnected = (sourceId === d.id || targetId === d.id);
            if (isConnected) {
                connectedNodeIds.add(sourceId === d.id ? targetId : sourceId);
            }
            return isConnected ? 1 : 0.1;
        }).style("stroke", l => {
             const sourceId = l.source.id || l.source;
             const targetId = l.target.id || l.target;
             return (sourceId === d.id || targetId === d.id) ? '#ff4500' : getLinkColor(l, data.nodes); // Highlight color OrangeRed
        });

        // Dim non-connected nodes and labels
        nodeGroup.style("opacity", n => connectedNodeIds.has(n.id) ? 1 : 0.2);
        label.style("opacity", n => connectedNodeIds.has(n.id) ? 1 : 0.2);


        // --- Tooltip Content Generation ---
        tooltip.style("opacity", 0.9); // Make tooltip visible
        let tooltipContent = `<h3>${d.id}</h3>`;

        if (d.isClass) {
            tooltipContent += `<p><span class="badge" style="background-color:${classColors[d.class]}">CATEGORY</span></p>`;
         } else if (d.relatedClasses && d.relatedClasses.length > 0) {
             tooltipContent += `<p style="margin-bottom: 8px;">Category Affinity:</p><div style="margin-bottom: 8px;">`;
            Object.entries(d.categoryPercentages || {})
                .sort((a, b) => b[1] - a[1]) // Sort by percentage descending
                .forEach(([cls, percentage]) => {
                const percent = Math.round(percentage * 100);
                if (percent > 0) { // Only show > 0%
                    tooltipContent += `<span class="badge" style="background-color:${classColors[cls] || defaultColor}; margin-right: 3px;">${cls} ${percent}%</span> `;
                }
            });
            tooltipContent += `</div>`;
         }

        tooltipContent += `<p>Appears in <strong>${d.count}</strong> article${d.count > 1 ? 's' : ''} on this date</p>`;

         if (d.articles && d.articles.length > 0) {
             tooltipContent += `<p style="margin-bottom: 3px;">Related Articles (${d.articles.length}):</p><ul>`;
            d.articles.slice(0, 10).forEach(article => { // Limit displayed articles
                 const title = article.title || 'No Title';
                 const website = article.website || 'Unknown Source';
                 tooltipContent += `<li><strong>${title.substring(0, 60)}${title.length > 60 ? '...' : ''}</strong> (${website})</li>`;
            });
             if (d.articles.length > 10) tooltipContent += `<li style="color: #666;">... and ${d.articles.length - 10} more</li>`;
             tooltipContent += `</ul>`;
         }

        tooltip.html(tooltipContent);

      })
      .on("mousemove", function(event, d) {
          // Tooltip positioning - adjust slightly to avoid cursor overlap
          const [mouseX, mouseY] = d3.pointer(event, graphContainer.node()); // Get pointer relative to container
          tooltip.style("left", (mouseX + 15) + "px")
                 .style("top", (mouseY - 10) + "px");
      })
      .on("mouseout", function(event, d) {
          // Reset highlights if not currently 'clicked' (persisted highlight)
           if (!d3.select(this).classed('clicked-highlight')) {
              resetHighlights(data);
          }
          tooltip.style("opacity", 0); // Hide tooltip
      })
      .on("click", function(event, d) {
           event.stopPropagation(); // Prevent background click reset

            // Toggle clicked state for persistent highlight
            const isClicked = d3.select(this).classed('clicked-highlight');
            // Clear previous clicked highlights first
            nodeGroup.classed('clicked-highlight', false);
            // Then set/unset for the current node
             d3.select(this).classed('clicked-highlight', !isClicked);

             if (!isClicked) {
                 // Apply persistent highlight (similar to mouseover, but won't clear on mouseout)
                const connectedNodeIds = new Set([d.id]);
                link.style("stroke-opacity", l => {
                    const sourceId = l.source.id || l.source;
                    const targetId = l.target.id || l.target;
                    const isConnected = (sourceId === d.id || targetId === d.id);
                    if (isConnected) connectedNodeIds.add(sourceId === d.id ? targetId : sourceId);
                    return isConnected ? 1 : 0.1;
                }).style("stroke", l => (connectedNodeIds.has(l.source.id || l.source) && connectedNodeIds.has(l.target.id || l.target)) ? '#ff4500' : getLinkColor(l, data.nodes));

                nodeGroup.style("opacity", n => connectedNodeIds.has(n.id) ? 1 : 0.2);
                label.style("opacity", n => connectedNodeIds.has(n.id) ? 1 : 0.2);

                 // --- Detailed Tooltip (can be same as mouseover or more detailed) ---
                 // You can reuse the mouseover content or add more details if needed
                 tooltip.style("opacity", 0.9); // Keep tooltip visible
                 const [mouseX, mouseY] = d3.pointer(event, graphContainer.node());
                 tooltip.style("left", (mouseX + 15) + "px")
                        .style("top", (mouseY - 10) + "px");
             } else {
                 // If clicking again, remove the persistent highlight
                 resetHighlights(data);
             }
      });
}

function setupLinkInteractions(data) {
     if (!link || !edgeInfo || !tooltip || !data || !data.nodes) return;

     link.on("mouseover", function(event, d) {
         const linkElement = d3.select(this);
         linkElement.raise(); // Bring link to front

         linkElement
             .attr("stroke-width", (Math.max(1, Math.sqrt(d.value) * 1.2)) + 1.5) // Thicken on hover
             .style("stroke-opacity", 1)
             .style("stroke", "#ff4500"); // Highlight color

         // Show edge info
         const sourceNode = data.nodes.find(n => n.id === (d.source.id || d.source));
         const targetNode = data.nodes.find(n => n.id === (d.target.id || d.target));
         edgeInfo.style("display", "block")
             .html(`<strong>${sourceNode?.id || '?'} ↔ ${targetNode?.id || '?'}</strong><br>
                    Count: ${d.value} article${d.value > 1 ? 's' : ''}`);

         // Position edge info
         const [mouseX, mouseY] = d3.pointer(event, graphContainer.node());
         edgeInfo.style("left", (mouseX + 10) + "px")
                .style("top", (mouseY - 30) + "px");
     })
     .on("mousemove", function(event) {
          // Edge info positioning update
          const [mouseX, mouseY] = d3.pointer(event, graphContainer.node());
          edgeInfo.style("left", (mouseX + 10) + "px")
                 .style("top", (mouseY - 30) + "px");
     })
     .on("mouseout", function(event, d) {
         // Reset style only if not clicked
         if (!d3.select(this).classed('clicked-highlight-link')) {
              d3.select(this)
                  .attr("stroke-width", Math.max(1, Math.sqrt(d.value) * 1.2)) // Reset width
                  .style("stroke-opacity", 0.6)
                  .style("stroke", getLinkColor(d, data.nodes)); // Reset color
         }
          edgeInfo.style("display", "none");
     })
     .on("click", function(event, d) {
         event.stopPropagation(); // Prevent background click reset

          // Clear previous link clicks
         link.classed('clicked-highlight-link', false);
         // Toggle clicked state for this link
         d3.select(this).classed('clicked-highlight-link', true);


         // Show detailed article list for the connection in the main tooltip
         const sourceNode = data.nodes.find(n => n.id === (d.source.id || d.source));
         const targetNode = data.nodes.find(n => n.id === (d.target.id || d.target));

         let content = `<h3>Connection: ${sourceNode?.id || '?'} — ${targetNode?.id || '?'}</h3>
                       <p>Appears together in <strong>${d.articles?.length || d.value}</strong> article${(d.articles?.length || d.value) > 1 ? 's' : ''} on this date</p>`;

         if (d.articles && d.articles.length > 0) {
             content += `<p style="margin-bottom: 3px;">Articles (${d.articles.length}):</p><ul>`;
             d.articles.slice(0, 15).forEach(article => { // Show a few more for links
                 const title = article.title || 'No Title';
                 const website = article.website || 'Unknown Source';
                 content += `<li><strong>${title.substring(0, 70)}${title.length > 70 ? '...' : ''}</strong> (${website})</li>`;
             });
             if (d.articles.length > 15) content += `<li style="color: #666;">... and ${d.articles.length - 15} more</li>`;
             content += `</ul>`;
         } else {
             content += `<p>(Article details not available for this link)</p>`
         }

         tooltip.html(content).style("opacity", 0.9); // Show tooltip

         // Position tooltip
         const [mouseX, mouseY] = d3.pointer(event, graphContainer.node());
         tooltip.style("left", (mouseX + 15) + "px")
                .style("top", (mouseY - 10) + "px");
     });
}


// Highlight reset function
function resetHighlights(data) {
     if (!link || !nodeGroup || !label || !data || !data.nodes) return; // Exit if elements don't exist

     // Clear clicked highlights
     nodeGroup.classed('clicked-highlight', false);
     link.classed('clicked-highlight-link', false);

     // Reset styles
     link.style("stroke", d => getLinkColor(d, data.nodes)) // Use current data to get link color
         .style("stroke-opacity", 0.6)
          .attr("stroke-width", d => Math.max(1, Math.sqrt(d.value) * 1.2)); // Reset width

     nodeGroup.style("opacity", 1)
         .select('circle, path') // Reset node stroke
         .attr('stroke', d => d.isClass ? "#333" : getNodeColor(d))
         .attr('stroke-width', d => d.isClass ? 1.5 : 0.5);

     label.style("opacity", 1).attr('font-weight', d => d.isClass ? "bold" : "normal"); //.style('fill', '#333');

     // Hide tooltips/info
     tooltip.style("opacity", 0);
     edgeInfo.style("display", "none");
}

// Helper to check node connectivity (needs current graph data's links)
// Not strictly needed if using the Set approach in mouseover, but can be useful
function isConnected(nodeA, nodeB, graphData) {
    if (!graphData || !graphData.links) return false;
    if (!nodeA || !nodeB) return false;
    if (nodeA.id === nodeB.id) return true; // A node is connected to itself

    const nodeA_id = nodeA.id;
    const nodeB_id = nodeB.id;

    return graphData.links.some(link => {
        const sourceId = link.source.id || link.source;
        const targetId = link.target.id || link.target;
        return (sourceId === nodeA_id && targetId === nodeB_id) ||
               (sourceId === nodeB_id && targetId === nodeA_id);
    });
}