// Initialize and check the passed server-side data
let day_data;
try {
    day_data = JSON.parse('{{ day_data | tojson | safe }}');
    if (typeof day_data !== 'object' || day_data === null) {
        throw new Error("Invalid data object.");
    }
    console.log("Day Data:", day_data);
} catch (error) {
    console.error("Error parsing day_data:", error);
    day_data = {};  // Fallback to an empty object to prevent further errors
}

// Ensure year and month are valid by initializing and logging
const year = {{ year }} || new Date().getFullYear();
const month = {{ month }} - 1 || new Date().getMonth();  // Adjust for JS zero-indexing
console.log("Year:", year, "Month:", month);
