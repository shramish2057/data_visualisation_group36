<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';

  let staticMapSvg, tooltip, staticMapData;
  let tilingMethod = 'treemapSquarify'; 

  let colorScaleRegions = d3.scaleOrdinal(d3.schemeTableau10);

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
    const staticMapOrders = await d3.csv('data/Orders.csv');
    const staticMapRegions = await d3.csv('data/Regions.csv');

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

    staticMapOrders.forEach(order => {
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

    if (!staticMapSvg) {
      staticMapSvg = d3.select('#statictreemap').append('svg')
            .attr('width', 1200)
            .attr('height', 800)  
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


    console.log("selectedTilingMethod", tilingMethod)
    const treemap = d3.treemap()
      .tile(d3[tilingMethod] || d3.treemapSquarify) 
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
      .attr("transform", d => `translate(${d.x0},${d.y0})`);

      leaf.append("rect")
        .attr("fill", d => {
          const regionColor = colorScaleRegions(d.parent.data.name);
          return getTerritoryColor(regionColor, d.data.quantity, d.parent.data.totalQuantity);
        })
        .attr("width", d => d.x1 - d.x0)
        .attr("height", d => d.y1 - d.y0)
        .on("mouseover", (event, d) => {
          tooltip.style("display", "block")
                .html(`Region: ${d.parent.data.name}<br>
                        Territory: ${d.data.name}<br>
                        Order Value: $${d.data.value}<br>
                        Quantity: ${d.data.quantity}`)
                .style("left", `${event.pageX}px`)
                .style("top", `${event.pageY}px`);
        })
        .on("mousemove", (event) => {
          tooltip.style("left", `${event.pageX + 10}px`)
                .style("top", `${event.pageY + 10}px`);
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

  onMount(() => {
    tooltip = d3.select("body").append("div")
               .attr("class", "tooltip")
               .style("position", "absolute")
               .style("z-index", "10")
               .style("display", "none")
               .style("padding", "10px")
               .style("background", "rgba(255, 255, 255, 0.8)")
               .style("border", "1px solid #000")
               .style("border-radius", "5px");

    loadDataForStaticTreemap();
  });

  $: if (staticMapSvg && staticMapData && tilingMethod) {
    console.log("Tiling method changed to:", tilingMethod); 
    drawStaticTreemap();
  }

</script>

<style>
  .tooltip {
    font-size: 14px;
  }
</style>

<h5>Tiling Method</h5>
<select bind:value={tilingMethod}>
  <option value="treemapSquarify">Squarify</option>
  <option value="treemapBinary">Binary</option>
  <option value="treemapSliceDice">Slice-dice</option>
  <option value="treemapSlice">Slice</option>
  <option value="treemapDice">Dice</option>
</select>
<div id="statictreemap"></div>
