<script>
  import Navbar from '../Navbar.svelte';
  import { onMount } from 'svelte';
  import * as d3 from 'd3';

  let staticMapSvg, comparisonSvg, tooltip, staticMapData;
  let tilingMethod = 'treemapSquarify'; 
  let selectedNodes = new Set();
  let dateRange = [];
  let startDate, endDate;

  let colorScaleRegions = d3.scaleOrdinal(d3.schemeTableau10);
  let colorScaleTerritories = d3.scaleOrdinal(d3.schemeTableau10);

  function formatDate(date) {
    return d3.timeFormat("%Y-%m-%d")(date);
  }

  function parseDate(dateString) {
    return d3.timeParse("%Y-%m-%d")(dateString);
  }

  function parseOrderValue(productPrices) {
    return productPrices.split(',').map(price => parseInt(price.trim())).reduce((a, b) => a + b, 0);
  }

  function parseQuantities(quantities) {
    return quantities.split(',')
                     .map(qty => parseInt(qty.trim()))
                     .filter(qty => !isNaN(qty))
                     .reduce((a, b) => a + b, 0);
  }

  function setupColorScaling() {
  let maxQuantity = 0;
  staticMapData.children.forEach(region => {
    region.children.forEach(territory => {
      if (territory.quantity > maxQuantity) {
        maxQuantity = territory.quantity;
      }
    });
  });

  getTerritoryColor = function(baseColor, quantity) {
    let maxQuantity = 0;
    staticMapData.children.forEach(region => {
      region.children.forEach(territory => {
        if (territory.quantity > maxQuantity) {
          maxQuantity = territory.quantity;
        }
      });
    });

    let relativeQuantity = quantity / maxQuantity;
    return d3.color(baseColor).darker(2 - 2 * relativeQuantity).formatHex(); 
  };

}

async function loadDataForStaticTreemap() {
    const staticMapOrders = await d3.csv('data/Orders.csv', d => {
      d.OrderDate = parseDate(d.OrderDate);
      return d;
    });
    const staticMapRegions = await d3.csv('data/Regions.csv');

    // Filter orders within selected date
    let filteredOrders = staticMapOrders.filter(d => (!startDate || d.OrderDate >= parseDate(startDate)) && (!endDate || d.OrderDate <= parseDate(endDate)));
    let regionStaticMap = new Map();

    staticMapRegions.forEach(regionData => {
      if (!regionStaticMap.has(regionData.Region)) {
        regionStaticMap.set(regionData.Region, { name: regionData.Region, children: [] });
      }
      regionStaticMap.get(regionData.Region).children.push({
        name: regionData.Territory,
        value: 0,
        quantity: 0
      });
    });

    filteredOrders.forEach(order => {
      const territoryName = order.Territory;
      for (const region of regionStaticMap.values()) {
        const territoryEntry = region.children.find(t => t.name === territoryName);
        if (territoryEntry) {
          territoryEntry.value += parseOrderValue(order.ProductPricesInCP);
          territoryEntry.quantity += parseQuantities(order.Quantities);
        }
      }
    });

    staticMapData = { name: "Root", children: Array.from(regionStaticMap.values()) };

    // Set the color scale for regions once and do not change it
    colorScaleRegions.domain(staticMapData.children.map(region => region.name));

    if (!staticMapSvg) {
      staticMapSvg = d3.select('#statictreemap').append('svg')
            .attr('width', 1200)
            .attr('height', 800)  
            .style('font', '10px sans-serif');
      comparisonSvg = d3.select('#comparisonChart').append('svg')
            .attr('width', 1200)
            .attr('height', 600)
            .style('font', '10px sans-serif');

      drawStaticTreemap();
    }
    setupColorScaling();
}


  function getTerritoryColor(baseColor, quantity) {
    let maxQuantity = 0;
    staticMapData.children.forEach(region => {
      region.children.forEach(territory => {
        if (territory.quantity > maxQuantity) {
          maxQuantity = territory.quantity;
        }
      });
    });

    let relativeQuantity = quantity / maxQuantity;
    return d3.color(baseColor).darker(2 - 2 * relativeQuantity).formatHex(); 
  };
  
  function drawStaticTreemap() {
    if (!staticMapData) return;

    const root = d3.hierarchy(staticMapData)
      .sum(d => d.value)
      .sort((a, b) => b.value - a.value);

    const treemap = d3.treemap()
      .tile(d3[tilingMethod])
      .size([1160, 740])
      .padding(1)
      .round(true);
    treemap(root);

    staticMapSvg.selectAll("g").remove(); 
    const leaf = staticMapSvg.append("g")
      .attr("transform", "translate(0,100)")
      .selectAll("g")
      .data(root.leaves())
      .join("g")
      .attr("transform", d => `translate(${d.x0},${d.y0})`)
      .on("click", (event, d) => {
        toggleSelection(d.data.name);
        updateComparisonPanel();
      });

    leaf.append("rect")
      .attr("fill", d => {
        const regionColor = colorScaleRegions(d.parent.data.name);
        return getTerritoryColor(regionColor, d.data.quantity, d.parent.data.totalQuantity);
      })
      .attr("width", d => d.x1 - d.x0)
      .attr("height", d => d.y1 - d.y0)
      .each(function(d) {
        if (selectedNodes.has(d.data.name)) {
          d3.select(this).style('stroke', 'black').style('stroke-width', 2);
        } else {
          d3.select(this).style('stroke', null);
        }
      })
      .on("mouseover", (event, d) => {
        tooltip.style("display", "block")
          .html(`Region: ${d.parent.data.name}<br>
                  Territory: ${d.data.name}<br>
                  Order Value: $${d.data.value}<br>
                  Quantity: ${d.data.quantity}`)
          .style("left", `${event.pageX}px`)
          .style("top", `${event.pageY}px`);
      })
      .on("mouseout", () => {
        tooltip.style("display", "none");
      });

    leaf.append("text")
      .attr("x", 5)
      .attr("y", 20)
      .style('font', '6px sans-serif')
      .text(d => `${d.data.name}`);

    drawLegend();
    updateComparisonPanel(); // Ensure the panel is updated
  }

  function toggleSelection(name) {
    if (selectedNodes.has(name)) {
      selectedNodes.delete(name);
    } else {
      selectedNodes.add(name);
    }
    // Redraw the treemap to update selections visually
    drawStaticTreemap();
  }

  function drawLegend() {
    const itemsPerRow = 5;  
    const horizontalSpacing = 150;  
    const verticalSpacing = 30;  

    const numItems = colorScaleRegions.domain().length;
    const numRows = Math.ceil(numItems / itemsPerRow);
    const effectiveItemsInRow = numItems > itemsPerRow ? itemsPerRow : numItems;
    const totalWidth = effectiveItemsInRow * horizontalSpacing;
    const startX = (1160 - totalWidth) / 2;  

    const legend = staticMapSvg.append("g")
      .attr("transform", `translate(${startX}, 10)`);

    const legendItem = legend.selectAll(null)
      .data(colorScaleRegions.domain())
      .enter()
      .append("g")
      .attr("transform", (d, i) => {
        const x = (i % itemsPerRow) * horizontalSpacing;
        const y = Math.floor(i / itemsPerRow) * verticalSpacing;
        return `translate(${x}, ${y})`;
      });

    legendItem.append("rect")
      .attr("width", 18)
      .attr("height", 18)
      .attr("fill", d => colorScaleRegions(d));

    legendItem.append("text")
      .attr("x", 24)
      .attr("y", 9)
      .attr("dy", ".35em")
      .text(d => d);
  }

  // Using d3.interpolateViridis for continuous color scale
  function getColor(index, total) {
    return d3.interpolateViridis(index / total);
  }

  function updateColorScale(data) {
    const territories = data.map(node => node.name);
    const total = territories.length;
    territories.forEach((territory, index) => {
        colorScaleTerritories(territory, getColor(index, total));
    });
  }

  function updateComparisonPanel() {
    if (!comparisonSvg || selectedNodes.size === 0) {
        comparisonSvg.selectAll("*").remove();
        return;
  }
    comparisonSvg.selectAll("*").remove();

    const data = Array.from(selectedNodes).map(name =>
      staticMapData.children.flatMap(region => region.children)
      .find(node => node.name === name));

    updateColorScale(data); // Pass the actual data to update colors
    const margin = { top: 80, right: 20, bottom: 100, left: 80 }; // More space for titles
    const width = 1200 - margin.left - margin.right;
    const height = 600 - margin.top - margin.bottom;

    const x = d3.scaleBand().rangeRound([0, width]).padding(0.1);
    const y = d3.scaleLinear().rangeRound([height, 0]);

    const g = comparisonSvg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    x.domain(data.map(d => d.name));
    y.domain([0, d3.max(data, d => d.value)]);

    const xAxisGroup = g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x));
    xAxisGroup.append("text")
        .attr("class", "axis-title")
        .attr("y", 50) 
        .attr("x", width / 2)
        .attr("text-anchor", "middle")
        .text("Territory Names");

    const yAxisGroup = g.append("g")
        .call(d3.axisLeft(y).ticks(10, "s"));
    yAxisGroup.append("text")
        .attr("class", "axis-title")
        .attr("transform", "rotate(-90)")
        .attr("y", -60) 
        .attr("dy", ".71em")
        .attr("text-anchor", "end")
        .text("Values");

        g.selectAll(".bar")
          .data(data)
          .enter().append("rect")
          .attr("class", "bar")
          .attr("x", d => x(d.name))
          .attr("width", x.bandwidth())
          .attr("y", d => y(d.value))
          .attr("height", d => height - y(d.value))
          .attr("fill", d => colorScaleTerritories(d.name)) 
          .on("mouseover", (event, d) => {
            tooltip.style("display", "block");
          })
          .on("mousemove", (event, d) => {
            tooltip.html(`Order Value: $${d.value}`)
                  .style("left", (event.pageX + 10) + "px")
                  .style("top", (event.pageY - 10) + "px");
          })
          .on("mouseout", () => {
            tooltip.style("display", "none");
          });

      comparisonSvg.append("text")
      .attr("class", "chart-title")
      .attr("x", 600) 
      .attr("y", 30) 
      .attr("text-anchor", "middle")
      .style("font-size", "18px")
      .style("font-weight", "bold") 
      .style("fill", "#333") 
      .text("Comparison of Order Values across Selected Territories");


      addBarLegend(data); 
  }

  function addBarLegend(data) {
      const legend = comparisonSvg.append("g")
        .attr("transform", "translate(150, 605)");

      // Adding the header for the bar graph legend
      legend.append("text")
        .attr("class", "legend-title")
        .attr("x", 420)
        .attr("y", -30)
        .style("font-size", "14px")
        .style("font-weight", "bold")
        .text("Selected Territories");

      const legendItems = legend.selectAll(".legend")
        .data(data.map(d => d.name)) 
        .enter().append("g")
        .attr("class", "legend")
        .attr("transform", (d, i) => `translate(${i * 150}, 0)`);

      legendItems.append("rect")
        .attr("width", 18)
        .attr("height", 18)
        .style("fill", d => colorScaleTerritories(d));
      legendItems.append("text")
        .attr("x", 24)
        .attr("y", 9)
        .attr("dy", ".35em")
        .text(d => d);
  }

  function handleDateChange() {
    loadDataForStaticTreemap();
  }

  onMount(async () => {
    const ordersData = await d3.csv('data/Orders.csv', d => {
      d.OrderDate = parseDate(d.OrderDate);
      return d;
    });

    dateRange = d3.extent(ordersData, d => d.OrderDate);
    startDate = formatDate(dateRange[0]); // Initialize to the full range
    endDate = formatDate(dateRange[1]);

    loadDataForStaticTreemap();
  });

  onMount(() => {
    staticMapSvg = d3.select('#statictreemap').append('svg')
            .attr('width', 1200)
            .attr('height', 900)  
            .style('font', '10px sans-serif');

    comparisonSvg = d3.select('#comparisonChart').append('svg')
            .attr('width', 1200)
            .attr('height', 650)
            .style('font', '10px sans-serif');

    loadDataForStaticTreemap().then(() => {
      drawStaticTreemap();
      setupColorScaling();
    });

    tooltip = d3.select("body").append("div")
               .attr("class", "tooltip")
               .style("position", "absolute")
               .style("z-index", "10")
               .style("display", "none")
               .style("padding", "10px")
               .style("background", "rgba(255, 255, 255, 0.8)")
               .style("border", "1px solid #000")
               .style("border-radius", "5px");
  });

  $: if (staticMapSvg && staticMapData && tilingMethod) {
    console.log("Tiling method changed to:", tilingMethod); 
    drawStaticTreemap();
  }
</script>


<Navbar />
<h3>Treemap for Order sales and Quantity through different Regions and subsequent Territories</h3>
<h4>Please click on specific territories to see comparision of order value across territories</h4>
<div class="tiling-method-container">
  <h5>Tiling Method</h5>
  <select class="selection" bind:value={tilingMethod}>
    <option value="treemapSquarify">Squarify</option>
    <option value="treemapBinary">Binary</option>
    <option value="treemapSliceDice">Slice-dice</option>
    <option value="treemapSlice">Slice</option>
    <option value="treemapDice">Dice</option>
  </select>
  <h5>Order date Range</h5>
  <input type="date" bind:value={startDate} on:change={handleDateChange} min={formatDate(dateRange[0])} max={formatDate(dateRange[1])}>
  <input type="date" bind:value={endDate} on:change={handleDateChange} min={formatDate(dateRange[0])} max={formatDate(dateRange[1])}>
</div>
<h3>Regions</h3>
<div id="statictreemap"></div>
<div id="comparisonChart"></div>

<style>
  .tooltip {
    font-size: 14px;
  }
  .bar {
    fill: steelblue;
  }
  .axis-title {
    fill: #333;
    font-size: 14px;
    font-family: 'Arial', sans-serif;
  }
  .chart-title {
    fill: #333;
    font-size: 24px; 
    font-weight: bold;
    font-family: 'Arial', sans-serif;
  }
  .tiling-method-container {
    display: flex; 
    align-items: center; 
    margin-bottom: 10px;
  }

  .tiling-method-container {
    display: flex;      
    justify-content: center; 
    align-items: center;
    width: 100%;         
  }

  .tiling-method-container h5 {
    margin-right: 20px;  
  }
  .selection {
    margin-right: 50px;  
  }

</style>





