
const scenarios = JSON.parse(document.getElementById("scenarios").innerText);

const btnOptimization = document.getElementById("btn_optimization");
const divOptimizationInfo = document.getElementById("optimization_info");
const divOptimizationProgress = document.getElementById("optimization_progress");

const SIMULATION_CHECK_TIME = 5000;

let runningTasks = [];


async function startOptimization() {
  if (runningTasks.length > 0) {
    await stopOptimization();
  }
  btnOptimization.innerText = "Optimierung gestartet...";
  btnOptimization.classList.add("disabled");
  divOptimizationInfo.hidden = false;

  for (const scenario of scenarios) {
    const data = new URLSearchParams(
      {
        scenario: "oeprom",
        parameters: JSON.stringify({renovation_scenario: scenario})
      }
    );
    const response = await fetch("/oemof/simulate", {
      method: "POST",
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: data.toString(),
    });
    if (response.status === 200) {
      const json = await response.json();
      runningTasks.push(json.task_id);
    } else {
      throw new Error(`Simulation not started. Response status: ${response.status}`);
    }
  }
  console.log(`Simulation started with task IDs: ${runningTasks}`);
  setTimeout(checkResults, SIMULATION_CHECK_TIME);
}


async function stopOptimization() {
  while (true) {
    const taskId = runningTasks.pop();
    if (taskId === undefined) {
      break;
    }
    const data = new URLSearchParams({task_id: taskId});
    const response = await fetch("/oemof/terminate", {
      method: "POST",
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: data.toString(),
    });
    if (response.status === 200) {
      console.log(`Simulation stopped for taskId: ${taskId}`);
    } else {
      throw new Error(`Error terminating simulation with task ID '${taskId}'. Response status: ${response.status}`);
    }
  }
}


async function checkResults() {
  let simulationIds = [];
  for (const taskId of runningTasks) {
    const response = await fetch("/oemof/simulate?task_id=" + taskId, {
      method: "GET"
    });
    if (response.status === 200) {
      const json = await response.json();
      if (json.simulation_id !== null) {
        simulationIds.push(json.simulation_id);
      }
    } else {
      throw new Error(`Simulation for task ID '${taskId}' not found: ${response.status}`);
    }
  }
  divOptimizationProgress.innerText = `${simulationIds.length} / ${scenarios.length} Simulationen abgeschlossen.`;
  if (simulationIds.length === runningTasks.length) {
    showResults(simulationIds);
  } else {
    setTimeout(checkResults, SIMULATION_CHECK_TIME);
  }
}


function showResults(simulationIds) {
  console.log(`Simulation result IDs: ${simulationIds}`);
}
