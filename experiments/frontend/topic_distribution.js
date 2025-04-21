function draw_hist(path, elem, tooltipobj) {
    // Determine if this is left or right histogram based on the element ID
    const isLeftChart = elem.includes("left");

    // Set theme-specific colors
    const themeColors = {
        left: {
            primary: "#2B5BDC",
            secondary: "#5478E4",
            light: "#EBF0FF"
        },
        right: {
            primary: "#DC2B3C",
            secondary: "#E45458",
            light: "#FFEBEE"
        },
        // Shared color palette for topics - using distinct colors that work well with both themes
        topics: [
            "#8A5CF5", // Purple
            "#29AB87", // Teal
            "#F7B500", // Gold
            "#FF8C42", // Orange
            "#5271FF", // Blue
            "#E83F6F", // Pink
            "#32936F", // Green
            "#66BFBF", // Cyan
            "#2E294E", // Dark Blue
            "#7F78D2" // Lavender
        ]
    };

    var margin = {
        top: 40,
        right: 160,
        bottom: 100,
        left: 80
    }; // Increased bottom/right margin for labels/legend

    // Select the container and clear previous contents
    var container = d3.select(elem);
    container.selectAll("*").remove(); // Clear previous SVG if any


    // Calculate dimensions based on viewBox, adjusted for margins
    var width = 800 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;


    // Parse the Data
    d3.json(path).then(function(data) {

        // Transform data to group by keyword
        function prepareHistogramData(data) {
            // First, get all unique dates
            const allDates = [...new Set(data.flatMap(topic =>
                topic.buckets.map(bucket => bucket.date)
            ))].sort();

            // Then create an array of objects with date and topic counts
            return allDates.map(date => {
                const dateData = {
                    date
                };

                data.forEach(topic => {
                    const bucket = topic.buckets.find(b => b.date === date);
                    dateData[topic.topic.text] = bucket ? bucket.count : 0;
                });
                return dateData;
            });
        }

        let transformedData = prepareHistogramData(data);


        // Get all unique keywords
        keywords = [...new Set(data.map(d => d.topic.text))];

        // Assign consistent colors to topics if they don't already have colors
        keywords.forEach((keyword, index) => {
            if (!topicColorMap[keyword]) {
                // Assign a color from our topic palette
                topicColorMap[keyword] = themeColors.topics[index % themeColors.topics.length];
            }
        });

        // Set up color scale using our consistent color mapping
        const color = d3.scaleOrdinal()
            .domain(keywords)
            .range(keywords.map(keyword => topicColorMap[keyword]));

        // Create SVG with proper responsive sizing
        var container = d3.select(elem);
        var svg = container
            .append("svg")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("viewBox", "0 0 800 500")
            .attr("preserveAspectRatio", "xMidYMid meet")
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // Calculate dimensions
        var width = 800 - margin.left - margin.right,
            height = 500 - margin.top - margin.bottom;



        // Convert aggregated data to array format suitable for d3.stack
        // And get a list of all unique topics found
        const allTopics = new Set();
        transformedData = Object.entries(transformedData).map(([date, topics]) => {
            Object.keys(topics).forEach(topic => {
                if (topic != "date") {
                    allTopics.add(topic)
                }
            });
            return {
                date,
                ...topics // Spread topic counts into the object
            };
        }).sort((a, b) => new Date(a.date) - new Date(b.date)); // Sort chronologically

        const uniqueTopics = Array.from(allTopics);

        if (transformedData.length === 0 || uniqueTopics.length === 0) {
            console.warn(`No processable data after filtering/aggregation for ${elem}.`);
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", height / 2)
                .attr("text-anchor", "middle")
                .style("font-size", "16px")
                .style("fill", "#777")
                .text("No topics found in the selected data.");
            return;
        }


        // Assign consistent colors to topics if they don't already have colors
        uniqueTopics.forEach((topic, index) => {
            if (!topicColorMap[topic]) {
                // Assign a color from our topic palette, cycling through if needed
                topicColorMap[topic] = themeColors.topics[index % themeColors.topics.length];
            }
        });

        // --- D3 Stack Layout ---
        const stack = d3.stack()
            .keys(uniqueTopics)
            .order(d3.stackOrderNone)
            .offset(d3.stackOffsetNone);

        // Calculate stack data - handle potential missing topics on certain dates
        const stackedData = stack(transformedData.map(d => {
            const entry = {
                date: d.date
            };
            uniqueTopics.forEach(topic => {
                if (topic != "date") {
                    entry[topic] = d[topic] || 0; // Ensure 0 count if topic missing for this date
                }
            });
            return entry;
        }));


        // --- Scales ---
        const x = d3.scaleBand()
            .domain(transformedData.map(d => d.date))
            .range([0, width])
            .padding(0.3);

        const maxY = d3.max(stackedData[stackedData.length - 1] || [], d => d[1]); // Find max Y value across all stacks
        const y = d3.scaleLinear()
            .domain([0, (maxY || 10) * 1.1]) // Add 10% padding, ensure domain > 0
            .range([height, 0]);

        // --- Axes and Grid ---
        // Add clean grid lines
        svg.append("g")
            .attr("class", "grid-lines")
            .selectAll("line")
            .data(y.ticks(5))
            .enter()
            .append("line")
            .attr("x1", 0)
            .attr("x2", width)
            .attr("y1", d => y(d))
            .attr("y2", d => y(d))
            .attr("stroke", "rgba(0,0,0,0.07)")
            .attr("stroke-dasharray", "3,3");

        // Add X axis
        svg.append("g")
            .attr("class", "axis x-axis")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x)
                .tickSize(0)
                .tickPadding(10)
                // Show fewer ticks if too many dates
                .tickValues(x.domain().filter((d, i) => !(i % Math.ceil(x.domain().length / 10))))
            )
            .selectAll("text")
            .attr("transform", "rotate(-45)")
            .style("text-anchor", "end")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "11px") // Slightly smaller for potentially many dates
            .style("fill", "#777777");

        // Add Y axis
        svg.append("g")
            .attr("class", "axis y-axis")
            .call(d3.axisLeft(y)
                .ticks(5)
                .tickSize(0)
                .tickPadding(10)
            )
            .selectAll("text")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "12px")
            .style("fill", "#777777");

        // Remove domain lines for cleaner look
        svg.selectAll(".axis path")
            .style("display", "none"); // Hide domain lines
        svg.selectAll(".axis line")
            .style("stroke", "rgba(0,0,0,0.1)");

        // Add axis labels
        svg.append("text")
            .attr("class", "axis-label")
            .attr("x", width / 2)
            .attr("y", height + margin.bottom - 25) // Adjust position
            .style("text-anchor", "middle")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "14px")
            .style("font-weight", "600")
            .style("fill", isLeftChart ? themeColors.left.primary : themeColors.right.primary)
            .text("Publication Date");

        svg.append("text")
            .attr("class", "axis-label")
            .attr("transform", "rotate(-90)")
            .attr("x", -height / 2)
            .attr("y", -margin.left + 20) // Adjust position
            .style("text-anchor", "middle")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "14px")
            .style("font-weight", "600")
            .style("fill", isLeftChart ? themeColors.left.primary : themeColors.right.primary)
            .text("Article Mention Frequency");

        // --- Draw Bars ---
        const bars = svg.append("g")
            .selectAll("g")
            .data(stackedData)
            .join("g")
            .attr("fill", d => color(d.key)) // Use the topic name (d.key) to get color
            .attr("class", d => `topic-group topic-${d.key.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`); // Class based on topic key

        bars.selectAll("rect")
            .data(d => d) // Bind the inner array (data for each date for this topic)
            .join("rect")
            .attr("x", d => x(d.data.date)) // Use date from d.data
            .attr("y", height) // Start from bottom for animation
            .attr("height", 0) // Start with height 0 for animation
            .attr("width", x.bandwidth())
            .attr("rx", 2) // Slightly rounded corners
            .attr("ry", 2)
            .attr("stroke", function() {
                const parentData = d3.select(this.parentNode).datum();
                const barColor = color(parentData.key);
                return d3.color(barColor).darker(0.3); // Slightly darker stroke
            })
            .attr("stroke-width", 0.5)
            .attr("class", function() {
                const parentData = d3.select(this.parentNode).datum();
                return `bar bar-${parentData.key.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`; // Bar class
            })
            // Animate bars on load
            .transition()
            .duration(700)
            .delay((d, i) => i * 50) // Stagger animation slightly
            .attr("y", d => y(d[1])) // Final Y position
            .attr("height", d => Math.max(0, y(d[0]) - y(d[1]))); // Final height, ensure non-negative


        // --- Tooltip and Interactivity ---
        const tooltip = d3.select(tooltipobj);

        bars.selectAll("rect")
            .on("mouseover", function(event, d) {
                const [y0, y1] = d; // Bar's start and end y values in the stack
                const parentData = d3.select(this.parentNode).datum(); // Data for the whole topic group
                const topic = parentData.key; // The topic name
                const date = d.data.date; // The date for this specific bar segment
                const count = y1 - y0; // The count for this topic on this date

                // Highlight current bar and fade others
                svg.selectAll(".bar")
                    .transition()
                    .duration(150)
                    .style("opacity", 0.3); // Fade all bars initially
                svg.selectAll(`.bar-${topic.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`) // Select bars of the same topic
                    .transition()
                    .duration(150)
                    .style("opacity", 0.7); // Highlight bars of the same topic slightly
                d3.select(this) // Highlight the specific hovered bar strongly
                    .transition()
                    .duration(150)
                    .style("opacity", 1)
                    .style("filter", "brightness(1.1)");

                // Show tooltip
                tooltip.transition()
                    .duration(200)
                    .style("opacity", 1);

                // Format the date nicely
                const formattedDate = new Date(date + "T00:00:00Z").toLocaleDateString('en-US', { // Add T00:00:00Z for UTC interpretation
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    timeZone: 'UTC' // Specify UTC timezone
                });

                // Use topic color in the tooltip header
                const topicColor = color(topic);

                let html = `
                    <div class="tooltip-header" style="background: ${topicColor}; padding: 8px 12px; border-radius: 4px 4px 0 0; margin: -10px -12px 8px -12px;">
                        <span style="color: white; font-weight: 600; font-size: 14px;">${topic}</span>
                    </div>
                    <div style="margin-bottom: 4px;">
                        <span style="font-weight: 600;">Date:</span> ${formattedDate}<br>
                        <span style="font-weight: 600;">Mentions:</span>
                        <span style="color: ${topicColor}; font-weight: 600;"> ${count}</span>
                    </div>`;

                tooltip.html(html)
                    .style("left", (event.pageX + 15) + "px")
                    .style("top", (event.pageY - 28) + "px")
                    .style("border", "none") // Remove border for cleaner look with header
                    .style("border-radius", "4px"); // Consistent radius
            })
            .on("mouseout", function() {
                // Reset all bars to full opacity and remove filter
                svg.selectAll(".bar")
                    .transition()
                    .duration(200)
                    .style("opacity", 1)
                    .style("filter", "none");

                // Hide tooltip
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            });


        // --- Legend ---
        const legendContainer = svg.append("g")
            .attr("class", "legend-container")
            // Position legend to the right of the chart
            .attr("transform", `translate(${width + 20}, 0)`);

        const legendItemHeight = 25; // Space between legend items
        const legendPadding = 10;
        const legendWidth = 140; // Fixed width for the legend box
        const legendScrollThreshold = Math.floor(height / legendItemHeight);

        const legend = legendContainer.append("g")
            .attr("class", "legend-items")
            .attr("transform", `translate(0, ${legendPadding})`);

        // Add legend items
        uniqueTopics.forEach((topic, i) => {
            // Only show a subset initially if too many topics, add note
            if (i >= legendScrollThreshold && uniqueTopics.length > legendScrollThreshold + 2) {
                if (i === legendScrollThreshold) { // Add note only once
                    legendContainer.append("text")
                        .attr("x", legendWidth / 2)
                        .attr("y", legendPadding + (i * legendItemHeight) + 10)
                        .attr("text-anchor", "middle")
                        .style("font-family", "'Inter', sans-serif")
                        .style("font-size", "10px")
                        .style("font-style", "italic")
                        .style("fill", "#777")
                        .text(`... and ${uniqueTopics.length - i} more topics`);
                }
                return; // Don't draw more items than threshold allows
            }

            const legendItem = legend.append("g")
                .attr("class", "legend-item")
                .attr("transform", `translate(0, ${i * legendItemHeight})`)
                .style("cursor", "pointer")
                .on("mouseover", function() {
                    // Highlight corresponding bars & legend item
                    const itemTopic = topic; // Capture topic in this scope
                    d3.select(this).select("text").style("font-weight", "bold");
                    svg.selectAll(".bar")
                        .transition().duration(150)
                        .style("opacity", 0.2);
                    svg.selectAll(`.bar-${itemTopic.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`)
                        .transition().duration(150)
                        .style("opacity", 1)
                        .style("filter", "brightness(1.1)");
                })
                .on("mouseout", function() {
                    // Reset styles
                    d3.select(this).select("text").style("font-weight", "normal");
                    svg.selectAll(".bar")
                        .transition().duration(150)
                        .style("opacity", 1)
                        .style("filter", "none");
                });

            legendItem.append("rect")
                .attr("width", 16)
                .attr("height", 16)
                .attr("rx", 3)
                .attr("ry", 3)
                .attr("fill", color(topic))
                .attr("stroke", d3.color(color(topic)).darker(0.2))
                .attr("stroke-width", 1);

            legendItem.append("text")
                .attr("x", 24)
                .attr("y", 8) // Center text vertically with the rect
                .attr("dy", "0.35em")
                // Truncate long topic names in legend
                .text(topic.length > 15 ? topic.substring(0, 14) + "…" : topic)
                .style("font-family", "'Inter', sans-serif")
                .style("font-size", "12px")
                .style("fill", "#333")
                .append("title") // Add full topic name as hover tooltip
                .text(topic);
        });


    }).catch(function(error) {
        console.error("Error loading or processing data:", error);
        // Display error message in the chart area
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "16px")
            .style("fill", "red")
            .text("Error loading data. Check console.");
    });
}