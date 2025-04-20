const topicColorMap = {};

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
            "#7F78D2"  // Lavender
        ]
    };
    
    var margin = {top: 30, right: 30, bottom: 80, left: 80};

    // Parse the Data
    const data = [{
            keyword: { text: "Climate Change", type: "Environment" },
            buckets: [{
                date: "2023-01-01",
                alignment: [{
                    value: "Outlet A",
                    count: 5,
                    mentioned_in: [{ id: 1, title: "Article 1" }, { id: 2, title: "Article 2" }]
                }, {
                    value: "Outlet B",
                    count: 3,
                    mentioned_in: [{ id: 3, title: "Article 3" }]
                }]
            }, {
                date: "2023-01-02",
                alignment: [{
                    value: "Outlet A",
                    count: 7,
                    mentioned_in: [{ id: 4, title: "Article 4" }, { id: 5, title: "Article 5" }]
                }, {
                    value: "Outlet C",
                    count: 2,
                    mentioned_in: [{ id: 6, title: "Article 6" }]
                }]
            }]
        }, {
            keyword: { text: "Economic Policy", type: "Politics" },
            buckets: [{
                date: "2023-01-01",
                alignment: [{
                    value: "Outlet B",
                    count: 4,
                    mentioned_in: [{ id: 7, title: "Article 7" }]
                }]
            }, {
                date: "2023-01-02",
                alignment: [{
                    value: "Outlet A",
                    count: 6,
                    mentioned_in: [{ id: 8, title: "Article 8" }, { id: 9, title: "Article 9" }]
                }, {
                    value: "Outlet C",
                    count: 3,
                    mentioned_in: [{ id: 10, title: "Article 10" }]
                }]
            }]
        }];

        // Transform data to group by keyword
        function transformData(data) {
            const result = {};

            // First organize by date
            data.forEach(keywordData => {
                const keyword = keywordData.keyword.text;

                keywordData.buckets.forEach(bucket => {
                    const date = bucket.date;

                    if (!result[date]) {
                        result[date] = {};
                    }

                    // Sum all counts for this keyword on this date
                    const totalCount = bucket.alignment.reduce((sum, a) => sum + a.count, 0);

                    result[date][keyword] = totalCount;
                });
            });

            // Convert to array format for D3
            return Object.entries(result).map(([date, keywords]) => {
                return {
                    date,
                    ...keywords
                };
            });
        }

        const transformedData = transformData(data);

        // Get all unique keywords
        const keywords = [...new Set(data.map(d => d.keyword.text))];

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

        // Prepare data for stacked bars
        const stack = d3.stack()
            .keys(keywords)
            .order(d3.stackOrderNone)
            .offset(d3.stackOffsetNone);

        const stackedData = stack(transformedData);

        // Scales
        const x = d3.scaleBand()
            .domain(transformedData.map(d => d.date))
            .range([0, width])
            .padding(0.3);

        const y = d3.scaleLinear()
            .domain([0, d3.max(stackedData[stackedData.length - 1], d => d[1]) * 1.1]) // Add 10% padding
            .range([height, 0]);

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

        // Add axes with styled appearance
        svg.append("g")
            .attr("class", "axis x-axis")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x)
                .tickSize(0)
            )
            .selectAll("text")
            .attr("transform", "rotate(-30)")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "12px")
            .style("fill", "#777777");
            
        // Remove domain lines
        svg.selectAll(".axis path")
            .style("stroke", "rgba(0,0,0,0.1)");
            
        svg.selectAll(".axis line")
            .style("stroke", "rgba(0,0,0,0.1)");

        svg.append("g")
            .attr("class", "axis y-axis")
            .call(d3.axisLeft(y)
                .ticks(5)
                .tickSize(0)
            )
            .selectAll("text")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "12px")
            .style("fill", "#777777");

        // Add axis labels with styled appearance
        svg.append("text")
            .attr("class", "axis-label")
            .attr("x", width / 2)
            .attr("y", height + margin.bottom - 15)
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
            .attr("y", -margin.left + 25)
            .style("text-anchor", "middle")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "14px")
            .style("font-weight", "600")
            .style("fill", isLeftChart ? themeColors.left.primary : themeColors.right.primary)
            .text("Mention Frequency");

        // Add chart title
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", -margin.top/2)
            .attr("text-anchor", "middle")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "16px")
            .style("font-weight", "bold")
            .style("fill", isLeftChart ? themeColors.left.primary : themeColors.right.primary)
            .text(isLeftChart ? "Topic Coverage in Left-leaning Media" : "Topic Coverage in Right-leaning Media");

        // Create bars with proper styling
        const bars = svg.append("g")
            .selectAll("g")
            .data(stackedData)
            .join("g")
            .attr("class", d => `keyword-group keyword-${d.key.replace(/\s+/g, '-')}`);

        // Add styled bars with animations
        bars.selectAll("rect")
            .data(d => d)
            .join("rect")
            .attr("x", d => x(d.data.date))
            .attr("y", height) // Start from bottom for animation
            .attr("height", 0) // Start with height 0 for animation
            .attr("width", x.bandwidth())
            .attr("rx", 3) // Rounded corners
            .attr("ry", 3) // Rounded corners
            .attr("fill", function() {
                const parentData = d3.select(this.parentNode).datum();
                return color(parentData.key);
            })
            .attr("stroke", function() {
                const parentData = d3.select(this.parentNode).datum();
                const barColor = color(parentData.key);
                // Create slightly darker stroke for definition
                return d3.color(barColor).darker(0.2);
            })
            .attr("stroke-width", 0.5)
            .attr("class", function() {
                const parentData = d3.select(this.parentNode).datum();
                return `bar bar-${parentData.key.replace(/\s+/g, '-')}`;
            })
            // Animate bars on load
            .transition()
            .duration(800)
            .delay((d, i) => i * 100)
            .attr("y", d => y(d[1]))
            .attr("height", d => y(d[0]) - y(d[1]));

        // Enhanced interactivity
        bars.selectAll("rect")
            .on("mouseover", function(event, d) {
                const [y0, y1] = d;
                const parentData = d3.select(this.parentNode).datum();
                const keyword = parentData.key;
                const date = d.data.date;
                const count = y1 - y0;

                // Highlight current bar and fade others
                svg.selectAll(".bar")
                    .transition()
                    .duration(200)
                    .style("opacity", function() {
                        const thisParentData = d3.select(this.parentNode).datum();
                        return thisParentData.key === keyword ? 1 : 0.3;
                    })
                    .style("filter", function() {
                        const thisParentData = d3.select(this.parentNode).datum();
                        return thisParentData.key === keyword ? "brightness(1.1)" : "none";
                    });

                // Find all articles for this keyword/date combination
                const articles = [];
                data.forEach(keywordData => {
                    if (keywordData.keyword.text === keyword) {
                        keywordData.buckets.forEach(bucket => {
                            if (bucket.date === date) {
                                bucket.alignment.forEach(a => {
                                    articles.push(...a.mentioned_in);
                                });
                            }
                        });
                    }
                });

                // Stylized tooltip
                const tooltip = d3.select(tooltipobj);
                tooltip.transition()
                    .duration(200)
                    .style("opacity", 1);

                // Format the date nicely
                const formattedDate = new Date(date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });

                // Use topic color in the tooltip header
                const topicColor = color(keyword);

                let html = `
                    <div class="tooltip-header" style="background: ${topicColor}; padding: 8px 12px; border-radius: 4px 4px 0 0; margin: -8px -12px 8px -12px;">
                        <span style="color: white; font-weight: 600; font-size: 14px;">${keyword}</span>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="font-weight: 600;">Date:</span> ${formattedDate}<br>
                        <span style="font-weight: 600;">Mentions:</span> 
                        <span style="color: ${topicColor}; font-weight: 600;">${count}</span>
                    </div>`;
                
                if (articles.length > 0) {
                    html += `<div style="font-weight: 600; margin-bottom: 4px; padding-top: 4px; border-top: 1px solid rgba(0,0,0,0.1);">Articles:</div>
                    <ul style="margin: 0; padding-left: 16px; font-size: 12px;">`;
                    
                    articles.slice(0, 3).forEach(article => {
                        html += `<li style="margin-bottom: 3px;">${article.title}</li>`;
                    });
                    
                    if (articles.length > 3) {
                        html += `<li style="color: #777;">...and ${articles.length - 3} more</li>`;
                    }
                    
                    html += `</ul>`;
                }

                tooltip.html(html)
                    .style("left", (event.pageX + 15) + "px")
                    .style("top", (event.pageY - 28) + "px")
                    .style("box-shadow", "0 4px 15px rgba(0,0,0,0.15)")
                    .style("border-radius", "4px")
                    .style("border", "none");
            })
            .on("mouseout", function() {
                // Reset all bars to full opacity
                svg.selectAll(".bar")
                    .transition()
                    .duration(200)
                    .style("opacity", 1)
                    .style("filter", "none");

                d3.select(tooltipobj)
                    .transition()
                    .duration(500)
                    .style("opacity", 0);
            });

        // Add styled legend with dynamic sizing
        const legendContainer = svg.append("g")
        .attr("class", "legend-container")
        .attr("transform", `translate(${width - 140}, 10)`);

        // Calculate legend dimensions based on number of topics
        const legendItemHeight = 28;
        const legendPadding = 15;
        const legendHeaderHeight = 30;
        const maxLegendHeight = height * 0.75; // Cap at 75% of chart height
        const totalItemsHeight = keywords.length * legendItemHeight;
        const legendHeight = Math.min(totalItemsHeight + legendHeaderHeight + legendPadding, maxLegendHeight);
        const shouldScroll = totalItemsHeight > (maxLegendHeight - legendHeaderHeight - legendPadding);

        // Create legend background with dynamic height
        legendContainer.append("rect")
        .attr("width", 130)
        .attr("height", legendHeight)
        .attr("fill", "white")
        .attr("rx", 6)
        .attr("ry", 6)
        .attr("stroke", isLeftChart ? themeColors.left.primary : themeColors.right.primary)
        .attr("stroke-width", 1)
        .attr("stroke-opacity", 0.3)
        .attr("fill-opacity", 0.9);

        // Add legend title
        legendContainer.append("text")
        .attr("x", 65)
        .attr("y", 20)
        .attr("text-anchor", "middle")
        .style("font-family", "'Inter', sans-serif")
        .style("font-size", "12px")
        .style("font-weight", "600")
        .style("fill", isLeftChart ? themeColors.left.primary : themeColors.right.primary)
        .text("Topics");

        // Create clipping path for scrollable area if needed
        if (shouldScroll) {
        legendContainer.append("defs")
            .append("clipPath")
            .attr("id", `legend-clip-${isLeftChart ? "left" : "right"}`)
            .append("rect")
            .attr("width", 110)
            .attr("height", legendHeight - legendHeaderHeight - 10)
            .attr("x", 10)
            .attr("y", legendHeaderHeight);
        }

        // Create legend group with potential scrolling
        const legend = legendContainer.append("g")
        .attr("class", "legend-items")
        .attr("transform", `translate(10, ${legendHeaderHeight})`)
        .style("overflow-y", shouldScroll ? "scroll" : "visible");

        if (shouldScroll) {
        legend.attr("clip-path", `url(#legend-clip-${isLeftChart ? "left" : "right"})`);
        }

        // Add topic count if there are many
        if (keywords.length > 10) {
        legendContainer.append("text")
            .attr("x", 65)
            .attr("y", legendHeight - 8)
            .attr("text-anchor", "middle")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "10px")
            .style("font-style", "italic")
            .style("fill", "#777")
            .text(`${keywords.length} topics total`);
        }

        // Add scroll hint if needed
        if (shouldScroll) {
        legendContainer.append("text")
            .attr("x", 120)
            .attr("y", legendHeight / 2)
            .attr("text-anchor", "end")
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "14px")
            .style("fill", "#999")
            .text("↕");
        }

        // Create legend items
        keywords.forEach((keyword, i) => {
        const legendItem = legend.append("g")
            .attr("class", "legend-item")
            .attr("transform", `translate(0, ${i * legendItemHeight})`)
            .style("cursor", "pointer")
            .on("mouseover", function() {
                // Highlight corresponding bars
                d3.select(this).select("rect")
                    .transition()
                    .duration(200)
                    .attr("stroke-width", 2);
                    
                d3.select(this).select("text")
                    .transition()
                    .duration(200)
                    .style("font-weight", "600");
                    
                // Highlight all bars with this keyword
                svg.selectAll(".bar")
                    .transition()
                    .duration(200)
                    .style("opacity", function() {
                        const parentData = d3.select(this.parentNode).datum();
                        return parentData.key === keyword ? 1 : 0.3;
                    })
                    .style("filter", function() {
                        const parentData = d3.select(this.parentNode).datum();
                        return parentData.key === keyword ? "brightness(1.1)" : "none";
                    });
            })
            .on("mouseout", function() {
                // Reset style
                d3.select(this).select("rect")
                    .transition()
                    .duration(200)
                    .attr("stroke-width", 1);
                    
                d3.select(this).select("text")
                    .transition()
                    .duration(200)
                    .style("font-weight", "normal");
                    
                // Reset all bars to full opacity
                svg.selectAll(".bar")
                    .transition()
                    .duration(200)
                    .style("opacity", 1)
                    .style("filter", "none");
            });

        // Add styled legend items using consistent color mapping
        legendItem.append("rect")
            .attr("width", 16)
            .attr("height", 16)
            .attr("rx", 3)
            .attr("ry", 3)
            .attr("fill", color(keyword))
            .attr("stroke", d3.color(color(keyword)).darker(0.2))
            .attr("stroke-width", 1);

        legendItem.append("text")
            .attr("x", 24)
            .attr("y", 8)
            .attr("dy", "0.35em")
            .text(keyword.length > 14 ? keyword.substring(0, 13) + "..." : keyword)
            .style("font-family", "'Inter', sans-serif")
            .style("font-size", "12px")
            .style("fill", "#333")
            .append("title")
            .text(keyword); // Show full text on hover
        });

        // If scrollable, add mouse wheel event for scrolling
        if (shouldScroll) {
        // This is handled with CSS since D3 can't easily create true scrollable areas
        // We'll add a class to enable custom scrolling behavior
        legend.classed("scrollable-legend", true);
        }
}
