function sortTable(columnIndex) {
    const table = document.getElementById("urunlerTable");
    const rows = Array.from(table.rows).slice(1); // Get all rows except the header

    if (!table.hasAttribute("data-sort-order")) {
        table.setAttribute("data-sort-order", "asc");
    }

    const isAscending = table.getAttribute("data-sort-order") === "asc";

    const headers = table.querySelector("thead tr").querySelectorAll("th");
    headers.forEach((header, index) => {
        header.classList.remove("asc", "desc");
        if (index === columnIndex) {
            header.classList.add(isAscending ? "asc" : "desc");
        }
    });

    const sortedRows = rows.sort((a, b) => {
        const cellA = a.cells[columnIndex].innerText.trim();
        const cellB = b.cells[columnIndex].innerText.trim();

        const isNumber = !isNaN(cellA) && !isNaN(cellB);
        return isNumber
            ? (isAscending ? cellA - cellB : cellB - cellA)
            : (isAscending
                ? cellA.localeCompare(cellB, 'tr')
                : cellB.localeCompare(cellA, 'tr'));
    });

    table.setAttribute("data-sort-order", isAscending ? "desc" : "asc");

    const tbody = table.querySelector("tbody");
    tbody.innerHTML = ""; // Clear existing rows
    sortedRows.forEach(row => tbody.appendChild(row)); // Append sorted rows
}
