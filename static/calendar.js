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

function dayRow () {
    const dayLabelsContainer = document.querySelector('.day-labels'); // Container for day labels
    dayLabelsContainer.innerHTML = '';
    daysOfWeek.forEach(day => {
        const dayLabel = document.createElement('div');
        dayLabel.className = 'day-label';
        dayLabel.textContent = day;
        daysRow.appendChild(dayLabel);
    });

    const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const daysRow = document.createElement('div');
    daysRow.className = 'days-row';


    // Insert the daysRow into the dayLabelsContainer
    dayLabelsContainer.appendChild(daysRow);

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
            if (value > 0) return 'positive clickable';
            if (value < 0) return 'negative clickable';
            return '';
        }

        function getValueClassBalance(value) {
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
                <div class="actual balance ${getValueClassBalance(actualBalance)}">${actualBalance.toFixed(2)}</div>
            </div>
            <div class="totals-column expected-column">
                <div>Expected</div>
                <div class="income ${getValueClass(expectedIncome)}">${expectedIncome.toFixed(2)}</div>
                <div class="expected bills ${getValueClass(expectedBills)}">${expectedBills.toFixed(2)}</div>
                <div class="expected expenses ${getValueClass(expectedExpenses)}">${expectedExpenses.toFixed(2)}</div>
                <div class="expected balance ${getValueClassBalance(expectedBalance)}">${expectedBalance.toFixed(2)}</div>
            </div>
        `;

        dateBox.append(dateHeader, totalsContainer);
        calendarGrid.appendChild(dateBox);

        // Ensure the elements exist before adding event listeners for actual/expected
        const incomeCell = dateBox.querySelector('.income');
        if (incomeCell && actualIncome > 0) {
            incomeCell.addEventListener('click', function() {
                const incomeDetails = dataForDay.actual_income_details || [];
                console.log(`Income details for ${formattedDate}:`, incomeDetails); // Log the details
                // Use the correct URL format with cleared=1 for actual entries
                const url = `/budget/get-details?date=${formattedDate}&entry_type=Income&cleared=1`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        showModal(formattedDate, 'Actual Income', data, 'actual');
                    })
                    .catch(error => {
                        console.error('Error fetching income details:', error);
                    });
            });
        }

        const billsCell = dateBox.querySelector('.actual.bills');
        if (billsCell && actualBills > 0) {
            billsCell.addEventListener('click', function() {
                const billsDetails = dataForDay.actual_bills_details || [];
                console.log(`Bills details for ${formattedDate}:`, billsDetails); // Log the details
                // Use the correct URL format with cleared=1 for actual entries
                const url = `/budget/get-details?date=${formattedDate}&entry_type=Bill&cleared=1`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        showModal(formattedDate, 'Actual Bills', data, 'actual');
                    })
                    .catch(error => {
                        console.error('Error fetching bills details:', error);
                    });
            });
        }

        const expensesCell = dateBox.querySelector('.actual.expenses');
        if (expensesCell && actualExpenses > 0) {
            expensesCell.addEventListener('click', function() {
                const expensesDetails = dataForDay.actual_expenses_details || [];
                console.log(`Expenses details for ${formattedDate}:`, expensesDetails); // Log the details
                // Use the correct URL format with cleared=1 for actual entries
                const url = `/budget/get-details?date=${formattedDate}&entry_type=Expense&cleared=1`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        showModal(formattedDate, 'Actual Expenses', data, 'actual');
                    })
                    .catch(error => {
                        console.error('Error fetching expenses details:', error);
                    });
            });
        }

        const balanceCell = dateBox.querySelector('.actual.balance');
        if (balanceCell && actualBalance > 0) {
            balanceCell.addEventListener('click', function() {
                const balanceDetails = dataForDay.actual_balance_details || [];
                console.log(`Balance details for ${formattedDate}:`, balanceDetails); // Log the details
                // Use the correct URL format with cleared=1 for actual entries
                const url = `/budget/get-details?date=${formattedDate}&entry_type=Balance&cleared=1`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        showModal(formattedDate, 'Actual Balance', data, 'actual');
                    })
                    .catch(error => {
                        console.error('Error fetching balance details:', error);
                    });
            });
        }

        // Similarly check for expected values...
        const expectedIncomeCell = dateBox.querySelector('.expected.income');
        if (expectedIncomeCell && expectedIncome > 0) {
            expectedIncomeCell.addEventListener('click', function() {
                const expectedIncomeDetails = dataForDay.expected_income_details || [];
                console.log(`Expected Income details for ${formattedDate}:`, expectedIncomeDetails); // Log the details
                // Use the correct URL format with cleared=0 for expected entries
                const url = `/budget/get-details?date=${formattedDate}&entry_type=Income&cleared=0`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        showModal(formattedDate, 'Expected Income', data, 'expected');
                    })
                    .catch(error => {
                        console.error('Error fetching expected income details:', error);
                    });
            });
        }

        const expectedBillsCell = dateBox.querySelector('.expected.bills');
        if (expectedBillsCell && expectedBills > 0) {
            expectedBillsCell.addEventListener('click', function() {
                const expectedBillsDetails = dataForDay.expected_bills_details || [];
                console.log(`Expected Bills details for ${formattedDate}:`, expectedBillsDetails); // Log the details
                // Use the correct URL format with cleared=0 for expected entries
                const url = `/budget/get-details?date=${formattedDate}&entry_type=Bill&cleared=0`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        showModal(formattedDate, 'Expected Bills', data, 'expected');
                    })
                    .catch(error => {
                        console.error('Error fetching expected bills details:', error);
                    });
            });
        }

        const expectedExpensesCell = dateBox.querySelector('.expected.expenses');
        if (expectedExpensesCell && expectedExpenses > 0) {
            expectedExpensesCell.addEventListener('click', function() {
                const expectedExpensesDetails = dataForDay.expected_expenses_details || [];
                console.log(`Expected Expenses details for ${formattedDate}:`, expectedExpensesDetails); // Log the details
                // Use the correct URL format with cleared=0 for expected entries
                const url = `/budget/get-details?date=${formattedDate}&entry_type=Expense&cleared=0`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        showModal(formattedDate, 'Expected Expenses', data, 'expected');
                    })
                    .catch(error => {
                        console.error('Error fetching expected expenses details:', error);
                    });
            });
        }

        const expectedBalanceCell = dateBox.querySelector('.expected.balance');
        if (expectedBalanceCell && expectedBalance > 0) {
            expectedBalanceCell.addEventListener('click', function() {
                const expectedBalanceDetails = dataForDay.expected_balance_details || [];
                console.log(`Expected Balance details for ${formattedDate}:`, expectedBalanceDetails); // Log the details
                // Use the correct URL format with cleared=0 for expected entries
                const url = `/budget/get-details?date=${formattedDate}&entry_type=Balance&cleared=0`;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        showModal(formattedDate, 'Expected Balance', data, 'expected');
                    })
                    .catch(error => {
                        console.error('Error fetching expected balance details:', error);
                    });
            });
        }
    }
}

function showModal(date, type, details, entryType) {
    console.log(`Showing modal for ${type} on ${date}`, details);

    const modalBody = document.getElementById('day-details-content');
    let detailsHTML = '';

    if (details && details.length > 0) {
        detailsHTML = details.map(item => `
            <tr>
                <td>${item.name || 'N/A'}</td>
                <td>$${item.amount ? item.amount.toFixed(2) : '0.00'}</td>

            </tr>
        `).join('');
    } else {
        detailsHTML = '<tr><td colspan="3">No details available.</td></tr>';
    }

    modalBody.innerHTML = `
        <H5>${date}</H5>
        <h5>${type}</h5>
        <table class="table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Amount</th>
                </tr>
            </thead>
            <tbody>
                ${detailsHTML}
            </tbody>
        </table>
    `;


    const modal = new bootstrap.Modal(document.getElementById('dayModal'));
    modal.show();
}

document.getElementById('prev-month-btn').addEventListener('click', () => updateMonth(-1));
document.getElementById('next-month-btn').addEventListener('click', () => updateMonth(1));
