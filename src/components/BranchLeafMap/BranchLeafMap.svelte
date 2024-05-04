async function loadData() {
  const orders = await d3.csv('data/orders.csv');
  const products = await d3.csv('data/products.csv');

  const mergedData = orders.map(order => {
    const product = products.find(product => product.product_code === order.productsIDs);
    const subtype = product ? product.Subtype : 'Unknown';
    const type = product ? product.Type : 'Unknown';
    const quantities = parseInt(quantities); // Convert quantity to integer

    return {
      ProductsIDs: productsIDs,
      Subtype: subtype,
      Type: type,
      Quantity: quantities
    };
  });

const groupedData = d3.rollups(mergedData, 
    v => d3.sum(v, d => d.Quantity), 
    d => [d.Type, d.Subtype]
  ).map(([key, value]) => ({
    Type: key[0],
    Subtype: key[1],
    Value: value
  }));

  return groupedData;
}

   
function TreeValue(
  data,
  {
    // data is either tabular (array of objects) or hierarchy (nested objects)
    path, // as an alternative to id and parentId, returns an array identifier, imputing internal nodes
    id = Array.isArray(data) ? (d) => d.id : null, // if tabular data, given a d in data, returns a unique identifier (string)
    parentId = Array.isArray(data) ? (d) => d.parentId : null, // if tabular data, given a node d, returns its parent’s identifier
    children, // if hierarchical data, given a d in data, returns its children
    format = ",", // format specifier string or function for values
    value = (d) => d.value, // given a node d, returns a quantitative value (for area encoding; null for count)
    sort = (a, b) => d3.descending(a.value, b.value), // how to sort nodes prior to layout
    label, // given a node d, returns the name to display on the rectangle
    title, // given a node d, returns its hover text
    link, // given a node d, its link (if any)
    linkTarget = "_blank", // the target attribute for links (if any)
    width = 640, // outer width, in pixels
    height = 400, // outer height, in pixels
    margin = 0, // shorthand for margins
    marginTop = margin, // top margin, in pixels
    marginRight = margin, // right margin, in pixels
    marginBottom = margin, // bottom margin, in pixels
    marginLeft = margin, // left margin, in pixels
    padding = 1, // cell padding, in pixels
    round = false, // whether to round to exact pixels
    color = d3.interpolateSpectral, // color scheme, if any
    fill = "#ccc", // fill for node rects (if no color encoding)
    fillOpacity = 1, // fill opacity for node rects
    stroke = "#555", // stroke for links
    strokeWidth = 1.5, // stroke width for links
    strokeOpacity = 0.4, // stroke opacity for links
    strokeLinejoin, // stroke line join for links
    strokeLinecap, // stroke line cap for links
    halo = "#fff", // color of label halo
    haloWidth = 3, // padding around the labels
    parentR = 3, // Radius for inner nodes
    drawLayout = false,
    minHeightForLabel = 10
  } = {}
) {
  // If id and parentId options are specified, or the path option, use d3.stratify
  // to convert tabular data to a hierarchy; otherwise we assume that the data is
  // specified as an object {children} with nested objects (a.k.a. the “flare.json”
  // format), and use d3.hierarchy.
  let root =
    path != null
      ? d3.stratify().path(path)(data)
      : id != null || parentId != null
      ? d3.stratify().id(id).parentId(parentId)(data)
      : d3.hierarchy(data, children).sort(sort);

  // Compute the values of internal nodes by aggregating from the leaves.
  value == null ? root.count() : root.sum((d) => Math.max(0, value(d)));

  // Compute formats.
  if (typeof format !== "function") format = d3.format(format);

  // Sort the leaves (typically by descending value for a pleasing layout).
  if (sort != null) root.sort(sort);

  // Compute the partition layout. Note that x and y are swapped!
  d3
    .partition()
    .size([height - marginTop - marginBottom, width - marginLeft - marginRight])
    .padding(padding)
    .round(round)(root);

  // Construct a color scale.
  if (color != null) {
    color = d3
      .scaleSequential([0, root.children.length - 1], color)
      .unknown(fill);
    root.children.forEach((child, i) => (child.index = i));
  }

  const descendants = root.descendants();

  // Radius scale
  let rScale = d3
    .scaleLinear()
    .domain([0, d3.max(descendants, (d) => d?.value)])
    .range([0.1, d3.max(descendants, (d) => (d.x1 - d.x0) / 2) - 1]);

  const svg = d3
    .create("svg")
    .attr("viewBox", [-marginLeft, -marginTop, width, height])
    .attr("width", width)
    .attr("height", height)
    .attr("overflow", "visible")
    .attr("style", "max-width: 100%; height: auto; height: intrinsic;")
    .attr("font-family", "sans-serif")
    .attr("font-size", 10);

  // Draw the Icicle
  if (drawLayout) {
    svg
      .append("g")
      .selectAll("rect")
      .data(descendants)
      .join("rect")
      .attr("y", (d) => d.x0)
      .attr("x", (d) => d.y0)
      .attr("height", (d) => d.x1 - d.x0)
      .attr("width", (d) => d.y1 - d.y0)
      .attr("fill", "none")
      .attr("stroke", stroke)
      .attr("stroke-opacity", strokeOpacity)
      .attr("stroke-linecap", strokeLinecap)
      .attr("stroke-linejoin", strokeLinejoin)
      .attr("stroke-width", strokeWidth);
  }

  // Links
  svg
    .append("g")
    .attr("fill", "none")
    .attr("stroke", stroke)
    .attr("stroke-opacity", strokeOpacity)
    .attr("stroke-linecap", strokeLinecap)
    .attr("stroke-linejoin", strokeLinejoin)
    .attr("stroke-width", strokeWidth)
    .selectAll("path")
    .data(root.links())
    .join("path")
    .attr(
      "d",
      d3
        .linkHorizontal()
        .x((d) => d.y0 + (d.y1 - d.y0) / 2)
        .y((d) => d.x0 + (d.x1 - d.x0) / 2)
    );

  const cell = svg
    .append("g")
    .selectAll("a")
    .data(descendants)
    .join("a")
    .attr("xlink:href", link == null ? null : (d) => link(d.data, d))
    .attr("target", link == null ? null : linkTarget)
    .attr(
      "transform",
      (d) => `translate(${d.y0 + +(d.y1 - d.y0) / 2},${d.x0})`
    );

  cell
    .append("circle")
    .attr("r", (d) => (!d.children ? rScale(d.value) : parentR))
    .attr("cy", (d) => rScale(d.value))
    .attr("fill", (d) =>
      !d.children
        ? color
          ? color(d.ancestors().reverse()[1]?.index)
          : fill
        : "none"
    )
    .attr("stroke", (d) =>
      d.children
        ? color
          ? color(d.ancestors().reverse()[1]?.index)
          : fill
        : "none"
    )
    .attr("fill-opacity", fillOpacity);

  const text = cell
    .filter((d) => d.x1 - d.x0 > minHeightForLabel)
    .append("text")
    .attr("text-anchor", (d) => (d.children ? "end" : "start"))
    .attr("x", (d) => (!d.children ? rScale(d.value) + 2 : -parentR - 2))
    .attr("y", (d) => (d.x1 - d.x0) / 2)
    .attr("paint-order", "stroke")
    .attr("stroke", halo)
    .attr("stroke-width", haloWidth)
    .attr("dy", "0.32em");

  if (label != null) text.append("tspan").text((d) => label(d.data, d));

  text
    .append("tspan")
    .attr("fill-opacity", 0.7)
    .attr("dx", label == null ? null : 3)
    .text((d) => format(d.value));

  if (title != null) cell.append("title").text((d) => title(d.data, d));

  return svg.node();
}

loadData().then(data => {
  chart = TreeValue(data, {
    id: d => d.Type + '|' + d.Subtype,
    parentId: d => null,
    value: d => d.Value,
    label: d => `${d.Type} - ${d.Subtype}`,
    title: (d, n) => `Type: ${d.Type}, Subtype: ${d.Subtype}, Value: ${n.value}`,
    width: 1152,
    height: 800
  });
});
