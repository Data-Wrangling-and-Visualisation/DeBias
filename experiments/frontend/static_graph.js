function createSandboxNetwork(options) {
    const {
        containerSelector,
        dataUrl,
        startDate,
        endDate,
        selectedTopics: selectedArticleTopicsFilter, // This is the filter for ARTICLES
        maxNodes,
        edgeThreshold,
        tooltipSelector
    } = options;

    const container = d3.select(containerSelector);
    if (container.empty()) {
        console.error(`Container element "${containerSelector}" not found.`);
        return;
    }
    container.selectAll("*").remove(); // Clear previous graph

    // --- Tooltip Setup ---
    let tooltip = d3.select(tooltipSelector || "#sandbox-tooltip");
    if (tooltip.empty()) {
        console.warn(`Tooltip element "${tooltipSelector || '#sandbox-tooltip'}" not found. Creating one.`);
        tooltip = d3.select('body').append('div')
            .attr('id', 'sandbox-tooltip')
            .attr('class', 'tooltip')
            .style('opacity', 0).style('position', 'absolute').style('pointer-events', 'none');
    } else {
         tooltip.style("opacity", 0); // Ensure it's hidden initially
    }

    // --- Modal Setup ---
    const modal = d3.select("#publication-modal");
    const modalTitle = d3.select("#modal-title");
    const publicationList = d3.select("#publication-list");
    const modalFooter = d3.select("#modal-footer");
    const closeButton = d3.select(".close-button");
     if (modal.empty()) {
         console.warn("Publication modal element not found. Article list on click will be disabled.");
     }

    // --- 1. Setup SVG ---
    const aspectRatio = 16 / 9;
    const baseWidth = 800;
    const baseHeight = baseWidth / aspectRatio;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const width = baseWidth - margin.left - margin.right;
    const height = baseHeight - margin.top - margin.bottom;

    const svg = container.append("svg")
        .attr("viewBox", `0 0 ${baseWidth} ${baseHeight}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .attr("width", "100%").attr("height", "100%").style("display", "block")
        .append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const linkGroup = svg.append("g").attr("class", "links");
    const nodeGroup = svg.append("g").attr("class", "nodes"); // Will contain node groups

    // --- 2. Load and Process Data ---
    d3.json(dataUrl).then(rawData => {
        if (!rawData || rawData.length === 0) {
            displayMessage("No data loaded."); return;
        }

        // --- 2a. Filter Data (Articles) ---
        const filteredArticles = rawData;

        if (filteredArticles.length === 0) {
            displayMessage("No articles match the selected filters."); return;
        }

        // --- 2b. Extract Nodes with NER Type AND Topic Distributions & Links ---
        // nodesMap: { lowerCaseKeyword -> { id, nerTypes: Map<type, count>, topics: Map<topic, count>, totalFreq, articles: Set } }
        let nodesMap = new Map();
        let linksCount = new Map(); // { lowerCaseId1 -> { lowerCaseId2 -> count } }

        filteredArticles.forEach(article => {
            const keyword = article.keyword.keyword.text;
            const mention = article.keyword.keyword.total_count;

            // Update nodesMap with NER types AND topics for each keyword mention

                if (!nodesMap.has(keyword)) {
                    nodesMap.set(keyword, {
                        id: keyword,
                        nerTypes: new Map(), // For NER type distribution (node color)
                        topics: new Map(),   // For news topic distribution (tooltip info)
                        totalFreq: 0,
                        articles: new Set()
                    });
                }
                const nodeEntry = nodesMap.get(keyword);
                nodeEntry.totalFreq += mention;
                article.mentioned_in.forEach(ment =>
                    {
                        nodeEntry.articles.add(ment.title);
                    })

                // Increment count for the specific NER type of this mention
                nodeEntry.nerTypes.set(article.keyword.keyword.type, (nodeEntry.nerTypes.get(article.keyword.keyword.type) || 0) + mention);

                // Increment count for each valid NEWS TOPIC of the article this keyword appeared in
                article.topics.forEach(topic => {
                    nodeEntry.topics.set(topic.text, (nodeEntry.topics.get(topic.text) || 0) + 1);
                });

                 // Ensure original ID uses first encountered casing
                 if (nodeEntry.id !== keyword && nodeEntry.totalFreq === mention) {
                     nodeEntry.id = keyword;
                 }

                 article.keyword.related.forEach(pair => {
                     const [id1, id2] = [keyword, pair.keyword.text].sort();
                        if (!linksCount.has(id1)) linksCount.set(id1, new Map());
                        linksCount.get(id1).set(id2, (linksCount.get(id1).get(id2) || 0) + pair.cooccurrence_count);
                 })
        });

        // --- Convert maps to arrays ---
        let nodes = Array.from(nodesMap.values());
        let links = [];
        linksCount.forEach((targets, sourceLowerId) => {
            targets.forEach((count, targetLowerId) => {
                if (count >= edgeThreshold) {
                    const sourceNode = nodesMap.get(sourceLowerId);
                    const targetNode = nodesMap.get(targetLowerId);
                    if (sourceNode && targetNode) {
                       links.push({ source: sourceNode.id, target: targetNode.id, value: count });
                    } else {
                         console.warn(`Node not found for link processing: ${sourceLowerId} or ${targetLowerId}`);
                    }
                }
            });
        });

        if (nodes.length === 0) { displayMessage("No keywords found after processing."); return; }
        if (links.length === 0) { displayMessage("No keyword connections found with current filters/threshold."); return; }

        // --- 2c. Prune Nodes ---
        const connectedNodeIds = new Set(links.flatMap(l => [l.source, l.target]));
        let filteredNodes = nodes.filter(node => connectedNodeIds.has(node.id));
        filteredNodes.sort((a, b) => b.totalFreq - a.totalFreq);
        filteredNodes = filteredNodes.slice(0, maxNodes);
        const finalNodeIds = new Set(filteredNodes.map(n => n.id));
        let finalLinks = links.filter(link => finalNodeIds.has(link.source) && finalNodeIds.has(link.target));
        let finalNodes = filteredNodes;

        if (finalNodes.length === 0 || finalLinks.length === 0) { displayMessage("No nodes/links remain after pruning."); return; }

        // --- Define Scales and Helpers BEFORE Simulation ---
        // NER Type Color Scale (for node rendering)
        const allNerTypes = new Set(finalNodes.flatMap(node => Array.from(node.nerTypes.keys())));
        const nerColorScale = d3.scaleOrdinal(d3.schemeCategory10).domain(Array.from(allNerTypes).sort());

        // News Topic Color Scale (for tooltip)
        const topicColorScale = d3.scaleOrdinal(d3.schemeTableau10).domain(NEWS_CATEGORIES);

        // Radius scale
        const maxFreq = d3.max(finalNodes, d => d.totalFreq) || 1;
        const radiusScale = d3.scaleSqrt().domain([1, maxFreq]).range([6, 24]).clamp(true);
        function calculateNodeRadius(nodeData) { return radiusScale(nodeData.totalFreq || 1); }

        // --- 3. D3 Force Simulation ---
        const simulation = d3.forceSimulation(finalNodes)
            .force("link", d3.forceLink(finalLinks).id(d => d.id)
                .distance(d => Math.max(45, 130 - d.value * 3 - (calculateNodeRadius(d.source) + calculateNodeRadius(d.target))/2))
                .strength(d => 0.03 + Math.min(0.3, d.value / 40)))
            .force("charge", d3.forceManyBody().strength(-90 - (finalNodes.length * 1.8)))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => calculateNodeRadius(d) + 5).strength(0.9));

        // --- 4. Draw Elements ---
        // Draw Links
        const link = linkGroup.selectAll("line").data(finalLinks, d => `${d.source.id}-${d.target.id}`)
            .join("line").attr("stroke", "#ccc").attr("stroke-opacity", 0.5)
            .attr("stroke-width", d => Math.min(8, 1 + Math.sqrt(d.value)));

        // Draw Node Groups (colored by NER type, pie charts for multiple NER types)
        const node = nodeGroup.selectAll("g.node-group").data(finalNodes, d => d.id)
            .join("g").attr("class", "node-group").attr("cursor", "pointer")
            .call(applyDragHandlers);

        // Append Circle OR Pie Chart based on nerTypes count
        node.each(function(d) {
            const group = d3.select(this);
            const radius = calculateNodeRadius(d);
            if (d.nerTypes.size <= 1) { // Treat 0 or 1 NER type as a single circle
                const nerType = d.nerTypes.size === 1 ? d.nerTypes.keys().next().value : 'UNKNOWN';
                group.append("circle").attr("r", radius)
                    .attr("fill", nerColorScale(nerType)) // Use NER color
                    .attr("stroke", d3.color(nerColorScale(nerType)).darker(0.7))
                    .attr("stroke-width", 1.5);
            } else {
                // Pie chart based on NER types, using nerColorScale
                drawPieChartNode(group, d.nerTypes, radius, nerColorScale, "type"); // Pass nerTypes map and key
            }
        });

        // Append Text Labels
        node.append("text").attr("class", "node-label").attr("dy", d => calculateNodeRadius(d) + 5)
            .text(d => d.id.length > 20 ? d.id.substring(0, 18) + "..." : d.id)
            .append("title").text(d => d.id);


        // --- 5. Interactivity ---
        node.on("mouseover", function(event, d) {
                const group = d3.select(this);
                group.select('circle, g.pie-node').transition().duration(150).attr('transform', 'scale(1.3)');
                group.select('text').style('font-weight', 'bold').style('font-size', '10px');

                tooltip.transition().duration(200).style("opacity", .95);

                // --- Tooltip showing NER Type(s) AND Topic Distribution ---
                 let typeHtml = ''; // For NER Types
                 if (d.nerTypes.size === 0) typeHtml = 'Type: N/A';
                 else if (d.nerTypes.size === 1) {
                     const nerType = d.nerTypes.keys().next().value;
                     typeHtml = `Type: <span style="font-weight: 500; color: ${nerColorScale(nerType)};">${nerType}</span>`;
                 } else {
                     typeHtml = 'Types:<ul style="margin: 3px 0 0 15px; padding: 0; font-size: 0.9em; list-style-type: none;">';
                     const sortedTypes = Array.from(d.nerTypes.entries()).sort(([, countA], [, countB]) => countB - countA);
                     sortedTypes.forEach(([type, count]) => {
                         typeHtml += `<li style="margin-bottom: 2px;"><span style="display: inline-block; width: 10px; height: 10px; background-color: ${nerColorScale(type)}; border-radius: 2px; margin-right: 5px;"></span>${type}: ${count}</li>`;
                     });
                     typeHtml += '</ul>';
                 }

                 let topicHtml = ''; // For News Topics
                 if (d.topics.size > 0) {
                     topicHtml = '<div style="margin-top: 8px; padding-top: 5px; border-top: 1px solid #eee; font-size: 0.9em;">Topic Distribution:<ul>';
                     const sortedTopics = Array.from(d.topics.entries()).sort(([, countA], [, countB]) => countB - countA);
                     sortedTopics.forEach(([topic, count]) => {
                         topicHtml += `<li style="margin-bottom: 2px; list-style-type: none;"><span style="display: inline-block; width: 10px; height: 10px; background-color: ${topicColorScale(topic)}; border-radius: 50%; margin-right: 5px;"></span>${topic}: ${count}</li>`;
                     });
                     topicHtml += '</ul></div>';
                 } else {
                     topicHtml = '<div style="margin-top: 5px; font-size: 0.9em; color: #888;">No topic data</div>';
                 }


                tooltip.html(`
                    <div style="font-weight: bold; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 4px;">${d.id}</div>
                    <div style="font-size: 0.85em; margin-bottom: 3px;">${typeHtml}</div> <!-- NER Type Info -->
                    <div style="font-size: 0.85em;">Total Freq: <span style="font-weight: 500;">${d.totalFreq}</span></div>
                    <div style="font-size: 0.8em; color: #666; margin-top: 4px;">(${d.articles.size} articles)</div>
                    ${topicHtml}  <!-- Topic Distribution Info -->
                    `)
                    .style("left", (event.pageX + 15) + "px")
                    .style("top", (event.pageY - 10) + "px");

                // Highlight links
                link.attr('stroke-opacity', l => (l.source.id === d.id || l.target.id === d.id) ? 0.9 : 0.1)
                    .attr('stroke', l => (l.source.id === d.id || l.target.id === d.id) ? '#777' : '#eee');
            })
            .on("mouseout", function(event, d) {
                 const group = d3.select(this);
                 group.select('circle, g.pie-node').transition().duration(150).attr('transform', 'scale(1)');
                 group.select('text').style('font-weight', 'normal').style('font-size', '9px');
                 tooltip.transition().duration(400).style("opacity", 0);
                 link.attr('stroke-opacity', 0.5).attr('stroke', '#ccc');
            })
            .on("click", function(event, d) {
                if (modal.empty()) {
                    console.log("Modal not found, cannot show articles.");
                    return;
                }
                 event.stopPropagation();
                 showPublicationModal(d);
            });

        // Modal close functionality
        if (!modal.empty()) {
            closeButton.on("click", () => modal.style("display", "none"));
            modal.on("click", function(event) { if (event.target === this) modal.style("display", "none"); });
        }

        // --- 6. Simulation Tick ---
        simulation.on("tick", () => {
            link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });

        // --- 7. Zooming ---
        const zoom = d3.zoom().scaleExtent([0.1, 8]).on("zoom", (event) => {
            svg.attr("transform", event.transform);
            const scale = event.transform.k;
            svg.selectAll('.node-label')
               .style('display', scale < 0.3 ? 'none' : 'block')
               .style('font-size', `${Math.min(12, Math.max(6, 9 / Math.sqrt(scale)))}px`);
        });
        d3.select(containerSelector).select('svg').call(zoom);

    }).catch(error => {
        console.error("Error loading or processing data:", error);
        displayMessage(`Error: ${error.message}. Check console.`);
    });

    // --- Helper Functions ---
    function displayMessage(message) {
        container.selectAll("*").remove();
        container.append("div")
            .style("display", "flex").style("align-items", "center").style("justify-content", "center")
            .style("height", "100%").style("min-height", "100px").style("color", "#777")
            .style("padding", "20px").style("text-align", "center").style("font-style", "italic")
            .text(message);
    }
    function applyDragHandlers(selection) {
        function dragstarted(event, d) { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; d3.select(this).raise(); }
        function dragged(event, d) { d.fx = event.x; d.fy = event.y; }
        function dragended(event, d) { if (!event.active) simulation.alphaTarget(0); /* Keep fixed: d.fx = null; d.fy = null; */ }
        selection.call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));
    }

    // --- Pie Chart Drawing Function (Generic) ---
    // Takes the data map (e.g., nerTypes or topics), radius, color scale, and the key name for data access
    function drawPieChartNode(nodeG, dataMap, radius, colorScale, dataKey) {
        const pieData = Array.from(dataMap.entries())
                              .map(([key, count]) => ({ [dataKey]: key, count })) // Use dynamic key
                              .sort((a,b) => b.count - a.count);

        const pie = d3.pie().value(d => d.count).sort(null);
        const arc = d3.arc().innerRadius(radius * 0.35).outerRadius(radius);

        const pieGroup = nodeG.append("g").attr("class", "pie-node");

        pieGroup.selectAll('path')
            .data(pie(pieData))
            .join('path')
            .attr('class', 'arc')
            .attr('d', arc)
            .attr('fill', d => colorScale(d.data[dataKey])) // Access data using dynamic key
            .append('title')
            .text(d => `${d.data[dataKey]}: ${d.data.count}`); // Access data using dynamic key
    }

    function showPublicationModal(nodeData) {
         if (modal.empty()) return; // Extra safety check
        modalTitle.text(`Articles mentioning "${nodeData.id}"`);
        publicationList.html("");
        const articlesToShow = Array.from(nodeData.articles).sort();
        const maxShown = 100;
        articlesToShow.slice(0, maxShown).forEach(title => { publicationList.append("li").text(title); });
        if (articlesToShow.length > maxShown) modalFooter.text(`Showing first ${maxShown} of ${articlesToShow.length} articles (alphabetical).`);
        else modalFooter.text(`${articlesToShow.length} article(s) found.`);
        modal.style("display", "block");
    }

} // End of createSandboxNetwork

// --- Event Listeners for Sandbox Controls ---
document.addEventListener('DOMContentLoaded', function() {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const nodeCountSlider = document.getElementById('node-count');
    const edgeThresholdSlider = document.getElementById('edge-threshold');

    function getSandboxSettings() {

        return {
            containerSelector: "#combined_network", dataUrl: "https://debias.api.dartt0n.ru/api/keywords/graph/",
            startDate: null, endDate: null,
            selectedTopics: [],
            maxNodes: 10, edgeThreshold: 2,
            tooltipSelector: "#sandbox-tooltip"
        };
    }

    // Initial graph load
    const initialSettings = getSandboxSettings();
    createSandboxNetwork(initialSettings);
});