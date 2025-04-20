function draw_hist(path, elem, tooltipobj) {
    var margin = {top: 10, right: 30, bottom: 20, left: 70};

    // append the svg object to the body of the pag
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

        // Set up color scale with more distinct colors
        const color = d3.scaleOrdinal()
            .domain(keywords)
            .range(d3.schemeTableau10);

        // Create SVG
        var svg = d3.select(elem)
        .append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .append("g")
        .attr("transform",
              "translate(" + margin.left + "," + margin.top + ")"),
        width = d3.select(elem)._groups[0][0].clientWidth * 0.8 - margin.left - margin.right,
        height = d3.select(elem)._groups[0][0].clientHeight - margin.top - margin.bottom;

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
            .padding(0.2);

        const y = d3.scaleLinear()
            .domain([0, d3.max(stackedData[stackedData.length - 1], d => d[1])])
            .range([height, 0]);

        // Add axes
        svg.append("g")
            .attr("class", "axis x-axis")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x))
            .selectAll("text")
            .attr("transform", "rotate(-45)")
            .style("text-anchor", "end");

        svg.append("g")
            .attr("class", "axis y-axis")
            .call(d3.axisLeft(y));

        // Add axis labels
        svg.append("text")
            .attr("class", "axis-label")
            .attr("x", width / 2)
            .attr("y", height + margin.bottom - 10)
            .style("text-anchor", "middle")
            .text("Date");

        svg.append("text")
            .attr("class", "axis-label")
            .attr("transform", "rotate(-90)")
            .attr("x", -height / 2)
            .attr("y", -margin.left + 15)
            .style("text-anchor", "middle")
            .text("Number of Mentions");

        // Add title
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", -20)
            .attr("text-anchor", "middle")
            .style("font-size", "16px")
            .style("font-weight", "bold")
            .text("Topic Coverage by Keyword");

        // Create bars with proper coloring
        const bars = svg.append("g")
            .selectAll("g")
            .data(stackedData)
            .join("g")
            .attr("class", d => `keyword-group keyword-${d.key.replace(/\s+/g, '-')}`);

        bars.selectAll("rect")
            .data(d => d)
            .join("rect")
            .attr("x", d => x(d.data.date))
            .attr("y", d => y(d[1]))
            .attr("height", d => y(d[0]) - y(d[1]))
            .attr("width", x.bandwidth())
            .attr("fill", function() {
                const parentData = d3.select(this.parentNode).datum();
                return color(parentData.key);
            })
            .attr("class", function() {
                const parentData = d3.select(this.parentNode).datum();
                return `bar bar-${parentData.key.replace(/\s+/g, '-')}`;
            })
            .on("mouseover", function(event, d) {
                const [y0, y1] = d;
                const parentData = d3.select(this.parentNode).datum();
                const keyword = parentData.key;
                const date = d.data.date;
                const count = y1 - y0;

                // Highlight all bars with this keyword
                svg.selectAll(".bar")
                    .transition()
                    .duration(200)
                    .style("opacity", function() {
                        const thisParentData = d3.select(this.parentNode).datum();
                        return thisParentData.key === keyword ? 1 : 0.3;
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

                const tooltip = d3.select(tooltipobj);
                tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);

                let html = `<strong>${keyword}</strong><br>`;
                html += `<strong>Date:</strong> ${date}<br>`;
                html += `<strong>Mentions:</strong> ${count}<br><br>`;
                html += `<strong>Articles:</strong><br>`;
                articles.slice(0, 5).forEach(article => {
                    html += `- ${article.title}<br>`;
                });
                if (articles.length > 5) {
                    html += `...and ${articles.length - 5} more`;
                }

                tooltip.html(html)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function() {
                // Reset all bars to full opacity
                svg.selectAll(".bar")
                    .transition()
                    .duration(200)
                    .style("opacity", 1);

                d3.select(tooltipobj)
                    .transition()
                    .duration(500)
                    .style("opacity", 0);
            });

        // Add legend with hover effects
        const legend = svg.append("g")
            .attr("class", "legend")
            .attr("transform", `translate(${width-20}, 0)`);

        keywords.forEach((keyword, i) => {
            const legendItem = legend.append("g")
                .attr("class", "legend-item")
                .attr("transform", `translate(0, ${i * 20})`)
                .on("mouseover", function() {
                    // Highlight all bars with this keyword
                    svg.selectAll(".bar")
                        .transition()
                        .duration(200)
                        .style("opacity", function() {
                            const parentData = d3.select(this.parentNode).datum();
                            return parentData.key === keyword ? 1 : 0.3;
                        });
                })
                .on("mouseout", function() {
                    // Reset all bars to full opacity
                    svg.selectAll(".bar")
                        .transition()
                        .duration(200)
                        .style("opacity", 1);
                });

            legendItem.append("rect")
                .attr("width", 18)
                .attr("height", 18)
                .attr("fill", color(keyword));

            legendItem.append("text")
                .attr("x", 24)
                .attr("y", 9)
                .attr("dy", "0.35em")
                .text(keyword)
                .style("font-size", "12px");
        });
}