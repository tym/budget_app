// Initialize currentDate with a default value, using the current year and month
let currentDate = new Date();

function updateMonth(offset) {
    currentDate.setMonth(currentDate.getMonth() + offset);
    console.log(`Updated currentDate: ${currentDate}`);
    
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1; // Adjust for zero-indexed month

    // Update the header with the new month and year
    document.getElementById('current-month').textContent = currentDate.toLocaleDateString('default', {
        year: 'numeric', month: 'long'
    });

    // Navigate to the new URL with updated parameters
    window.location.href = `/budget?year=${year}&month=${month}`;
}



function populateCalendar(year, month, day_data) {
    console.log(`Populating calendar for year: ${year}, month: ${month}`);
    console.log("Day Data:", day_data);

    const calendarGrid = document.getElementById('calendar-grid');
    const weeklyLabelsContainer = document.querySelector('.weekly-labels');
    
    // Clear existing content
    calendarGrid.innerHTML = '';
    weeklyLabelsContainer.innerHTML = '';

    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);
    const startDay = firstDay.getDay();

    // Add empty boxes for days before the first of the month
    for (let i = 0; i < startDay; i++) {
        const emptyBox = document.createElement('div');
        emptyBox.className = 'date-box empty';
        calendarGrid.appendChild(emptyBox);
    }

    // Add the labels dynamically based on the number of weeks in the month
    const totalDays = lastDay.getDate();
    const numberOfWeeks = Math.ceil((totalDays + startDay) / 7);
    
    for (let week = 0; week < numberOfWeeks; week++) {
        const labelSet = document.createElement('div');
        labelSet.className = 'label-set';

        const labelHeader = document.createElement('div');
        labelHeader.className = 'label-header';

        const labelContainer = document.createElement('div');
        labelContainer.className = 'label-container';

        // Create label elements for the set: Income, Bills, Expenses, Balance
        const labels = ['Income', 'Bills', 'Expenses', 'Balance'];
        labels.forEach(label => {
            const labelDiv = document.createElement('div');
            labelDiv.className = 'weekly-label';
            labelDiv.textContent = label;
            labelSet.appendChild(labelDiv);
        });
        weeklyLabelsContainer.append(labelContainer);
        labelContainer.append(labelHeader, labelSet);
    }

    // Add day boxes with data
    for (let day = 1; day <= lastDay.getDate(); day++) {
        const dateBox = document.createElement('div');
        dateBox.className = 'date-box';

        const dateHeader = document.createElement('div');
        dateHeader.className = 'date-header';
        dateHeader.textContent = day;

        const totalsContainer = document.createElement('div');
        totalsContainer.className = 'totals-container';

        // Format the current day as a string (e.g., '2024-12-01')
        const formattedDate = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dataForDay = day_data[formattedDate] || {};

        console.log(`Data for date ${formattedDate}:`, dataForDay);

        const actualIncome = dataForDay.actual_income || 0;
        const actualBills = dataForDay.actual_bills || 0;
        const actualExpenses = dataForDay.actual_expenses || 0;
        const actualBalance = dataForDay.actual_balance || 0;

        const expectedIncome = dataForDay.expected_income || 0;
        const expectedBills = dataForDay.expected_bills || 0;
        const expectedExpenses = dataForDay.expected_expenses || 0;
        const expectedBalance = dataForDay.expected_balance || 0;

        // Helper function to determine the class based on the value
        function getValueClass(value) {
            if (value > 0) return 'positive';
            if (value < 0) return 'negative';
            return '';
        }

        totalsContainer.innerHTML = `
            <div class="totals-column actual-column">
                <div>Actual</div>
                <div class="income ${getValueClass(actualIncome)}">${actualIncome.toFixed(2)}</div>
                <div class="actual bills ${getValueClass(actualBills)}">${actualBills.toFixed(2)}</div>
                <div class="actual expenses ${getValueClass(actualExpenses)}">${actualExpenses.toFixed(2)}</div>
                <div class="actual balance ${getValueClass(actualBalance)}">${actualBalance.toFixed(2)}</div>
            </div>
            <div class="totals-column expected-column">
                <div>Expected</div>
                <div class="income ${getValueClass(expectedIncome)}">${expectedIncome.toFixed(2)}</div>
                <div class="expected bills ${getValueClass(expectedBills)}">${expectedBills.toFixed(2)}</div>
                <div class="expected expenses ${getValueClass(expectedExpenses)}">${expectedExpenses.toFixed(2)}</div>
                <div class="expected balance ${getValueClass(expectedBalance)}">${expectedBalance.toFixed(2)}</div>
            </div>
        `;

        dateBox.append(dateHeader, totalsContainer);
        calendarGrid.appendChild(dateBox);
    }
}


document.getElementById('prev-month-btn').addEventListener('click', () => updateMonth(-1));
document.getElementById('next-month-btn').addEventListener('click', () => updateMonth(1));


function updateMonth(offset) {
    currentDate.setMonth(currentDate.getMonth() + offset);
    console.log(`Updated currentDate: ${currentDate}`);
    
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1; // Adjust for zero-indexed month

    // Update the header with the new month and year
    document.getElementById('current-month').textContent = currentDate.toLocaleDateString('default', {
        year: 'numeric', month: 'long'
    });

    // Navigate to the new URL with updated parameters
    window.location.href = `/budget?year=${year}&month=${month}`;
}

