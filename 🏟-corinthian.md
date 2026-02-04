# 🏟 Corinthian — Execution 🟢

> **Domain**: Runtime, actions, what HAPPENS, user interactions
> **Phase**: 4 of 7 — The ornate column where activity occurs
> **Architectural Style**: Ornate, active, performing

---

## 🏟📍🦉🧈➕🔵 SCL Interpreter District

The engine that parses and executes Semantic Compression Language.

### 🏟🦉📍🔵 - Interpreter Architecture.parti

```
┌─────────────────────────────────────────────────────────────┐
│                    SCL Interpreter                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐                                            │
│  │   Lexer     │  Text → Tokens                             │
│  │             │  "🐂📍 x 0" → [🐂, 📍, x, 0]              │
│  └──────┬──────┘                                            │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │   Parser    │  Tokens → AST                              │
│  │             │  {type: "init", action: "place", ...}      │
│  └──────┬──────┘                                            │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │  Validator  │  Type/reference checking                   │
│  │             │  Ensure valid before execution             │
│  └──────┬──────┘                                            │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │  Executor   │  Do the thing                              │
│  │             │  state.set("x", 0)                         │
│  └──────┬──────┘                                            │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │   State     │  Track all runtime state                   │
│  │   Manager   │  Variables, scopes, history                │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

```typescript
interface SCLInterpreter {
  // Pipeline
  lexer: Lexer
  parser: Parser
  validator: Validator
  executor: Executor
  stateManager: StateManager
  
  // Execute
  execute(source: string, context: ExecutionContext): ExecutionResult
  executeLine(line: string, context: ExecutionContext): LineResult
}
```

---

### 🏟🦉📍🔵 - Core Operations.parti

**Variables (🐂📍 init place):**
```scl
🐂📍 x 0                    ← create x, set to 0
🐂📍 name "Alex"            ← create string variable
🐂📍 items []               ← create empty list
🐂📍 config {}              ← create empty map
```

**Input (🧲 capture):**
```scl
🧲🪡 name                   ← pull input from user
🧲🪡 name "Enter name:"    ← with prompt message
🧲🪡 age "Enter age:"       ← typed input
```

**Output (🚀 dispatch):**
```scl
🚀🛒 "Hello"                ← push text to display
🚀🛒 variable               ← push variable value
🚀🛒🎯 blockRef "text"      ← push to specific block
```

**Logic (🦉 parse):**
```scl
🦉 x > 10                   ← evaluate condition
🦉 name === "Alex"          ← equality check
🦉 active                   ← truthy check
🦉 items.length > 0         ← property access
```

**Math (➕➖):**
```scl
➕ x 1                      ← add 1 to x
➖ x 1                      ← subtract 1 from x
➕ total price             ← add price to total
➖ inventory sold          ← subtract sold from inventory
```

**Control Flow:**
```scl
🦉 condition ↳              ← if true, execute indented block
  🚀🛒 "Yes!"
↳                           ← else branch
  🚀🛒 "No!"

🦋 items ↳                  ← for each in items
  🚀🛒 item

🦋 5 ↳                      ← repeat 5 times
  🤌🎯 action

🖼                          ← return/exit current block
⚫                          ← end/complete execution
```

**Navigation (🧸 channel):**
```scl
🧸 🎯blockZip               ← go to zip address
🧸 ↑                       ← go connected up
🧸 ↓                       ← go connected down
🧸 ←                       ← go connected left
🧸 →                       ← go connected right
🧸 🏠                      ← go home (origin)
```

**Timing (🪵 hold):**
```scl
🪵 1000                     ← pause 1000ms
⌛🦋 1000 ↳                 ← every 1000ms, execute block
  🤌🎯 update
⌛🪵                        ← stop timer
```

---

## 🏟📍🐍🧈➕🔵 Python Bridge District

### 🏟🐍📍🔵 - Bridge Architecture.parti

```
SCL Context              Python Runtime
┌───────────┐           ┌───────────────┐
│ Variables │ ── 🧸🛒 ──▶│ Python Globals│
│ score: 10 │           │ score = 10    │
└───────────┘           └───────┬───────┘
                                │
                        ┌───────▼───────┐
                        │ Execute Code  │
                        │ (Pyodide)     │
                        └───────┬───────┘
                                │
┌───────────┐                   │
│ Variables │ ◀── 🧲🪡 ─────────┘
│ result: ? │         Return values
└───────────┘
```

```typescript
interface PythonBridge {
  // Variable exchange
  pushToPython(name: string, value: any): void
  pullFromPython(name: string): any
  
  // Execution
  execute(code: string): ExecutionResult
  
  // Context
  globals: Map<string, any>
  libraries: string[]  // Available imports
}
```

---

### 🏟🐍📍🔵 - Code Block Syntax.parti

```
┌─────────────────────────────────┐
│ 🐍 Python                       │
├─────────────────────────────────┤
│ import math                     │
│                                 │
│ # 🧲 pulls SCL variables in    │
│ radius = 🧲radius               │
│                                 │
│ area = math.pi * radius ** 2   │
│                                 │
│ # 🚀 pushes results back       │
│ 🚀area                          │
└─────────────────────────────────┘
```

**Syntax Conventions:**
- `🧲variable` — Pull SCL variable into Python
- `🚀variable` — Push Python variable back to SCL
- Standard Python syntax otherwise

---

### 🏟🐍📍🟢 - Pyodide Integration.parti

```typescript
interface PyodideConfig {
  // Runtime
  runtime: 'Pyodide'        // Python compiled to WebAssembly
  environment: 'browser'    // Runs in browser
  sandboxed: true           // Isolated execution
  
  // Libraries
  availableLibraries: [
    'math',
    'random',
    'datetime',
    'json',
    're',
    // Plus user-loaded packages
  ]
  
  // Performance
  loadTime: '~2s'           // Initial load
  memoryLimit: '256MB'      // Per session
}
```

---

## 🏟📍🤌🧈➕🔵 Trigger Execution District

### 🏟🤌📍🔵 - Execution Flow.parti

```
Trigger Fires
    ↓
Find Connection → Check Condition
    ↓               ↓
  [yes]           [no] → stop
    ↓
Get Action → Get Target → Build Context
    ↓
Execute Action
    ↓
┌────────┬─────────┬────────┐
│Navigate│ Execute │ Other  │
│(go to) │ (run)   │(set/   │
│        │         │show/   │
│        │         │hide)   │
└────────┴─────────┴────────┘
```

```typescript
interface TriggerExecution {
  // Flow
  fire(trigger: Trigger): void
  checkCondition(condition: Condition): boolean
  buildContext(trigger: Trigger): ExecutionContext
  executeAction(action: Action, context: ExecutionContext): void
  
  // Action types
  actions: {
    navigate: (target: Target) => void
    execute: (target: BlockId) => void
    show: (target: BlockId) => void
    hide: (target: BlockId) => void
    set: (name: string, value: any) => void
    call: (toolId: string, inputs: any) => any
  }
}
```

---

### 🏟🤌📍🔵 - Event Queue.parti

```typescript
interface EventQueue {
  // Queue management
  queue: Event[]
  maxSize: 100
  
  // Processing
  scheduler: 'fifo' | 'priority'
  processOneAtATime: true
  
  // Event structure
  event: {
    type: EventType
    timestamp: number
    source: BlockId
    data: any
  }
}
```

**Queue Behavior:**
- Events wait in queue
- Scheduler picks next
- Process one at a time
- Condition check before execute

---

### 🏟🤌📍🔵 - Block Execution Context.parti

```typescript
interface ExecutionContext {
  // Identity
  block: Block              // Which block is executing
  trigger: Trigger          // What fired
  
  // State
  globals: Map<string, any> // Global variables
  locals: Map<string, any>  // Block-local state
  inputs: Map<string, any>  // Trigger inputs
  
  // Output interface
  output: {
    display: (value: any) => void
    set: (name: string, value: any) => void
    navigate: (target: Target) => void
    call: (toolId: string, inputs: any) => any
  }
  
  // Canvas access
  canvas: {
    getBlock: (id: BlockId) => Block
    getBlockByZip: (zip: ZipCode) => Block[]
    getVariable: (name: string) => any
    setVariable: (name: string, value: any) => void
  }
}
```

---

## 🏟📍🧸🧈➕🔵 Navigation District

### 🏟🧸📍🔵 - Connection Ports.parti

```
            top
             │
      ┌──────┴──────┐
      │             │
left ─┤   center    ├─ right
      │             │
      └──────┬──────┘
             │
           bottom
```

| Port | Typical Use | Symbol |
|------|-------------|--------|
| center | General purpose | ● |
| top | "Previous", "back" | ↑ |
| bottom | "Next", "forward" | ↓ |
| left | "Alternative", sidebar | ← |
| right | "Details", actions | → |

```typescript
interface ConnectionPort {
  position: 'top' | 'bottom' | 'left' | 'right' | 'center'
  symbol: string
  typicalUse: string
}
```

---

### 🏟🧸📍🔵 - Navigation Modes.parti

| Mode | Behavior | Use Case |
|------|----------|----------|
| fullscreen | Target fills viewport | Focus on single block |
| scroll | Smooth pan to target | Show context |
| warp | Instant jump | Zip routing, no animation |

```typescript
interface Navigation {
  modes: {
    fullscreen: (target: BlockId) => void
    scroll: (target: BlockId) => void
    warp: (target: BlockId | ZipCode) => void
  }
}
```

---

### 🏟🧸📍🔵 - Zip Routing.parti

```typescript
interface ZipRouting {
  // Navigate by zip
  navigateToZip(zip: ZipCode): void
  
  // Multiple blocks at same zip
  multipleMatchBehavior: 'first' | 'list' | 'nearest'
  
  // Examples
  examples: {
    'go to zip': '🧸 🎯🐂🧲🛒🟡'
    'go up': '🧸 ↑'
    'go home': '🧸 🏠'
  }
}
```

---

## 🏟📍🚀🧈➕🔵 Tool Execution District

### 🏟🚀📍🔵 - Tool Interaction Flow.parti

```
UI Event (button press)
    ↓
Get UI Event → Find Handler
    ↓
Gather Inputs → Execute Handler
    ↓
Update Outputs → Update UI
```

```typescript
interface ToolExecution {
  // Flow
  handleUIEvent(event: UIEvent): void
  findHandler(event: UIEvent): Handler
  gatherInputs(handler: Handler): InputValues
  executeHandler(handler: Handler, inputs: InputValues): OutputValues
  updateUI(outputs: OutputValues): void
}
```

---

### 🏟🚀📍🔵 - Tool State.parti

```typescript
interface ToolState {
  inputValues: Map<InputId, any>
  outputValues: Map<OutputId, any>
  internalState: Map<string, any>
  
  // Lifecycle
  initialized: boolean
  executing: boolean
  error: Error | null
}

// Example: Calculator Tool
{
  inputValues: {
    'a': 5,
    'b': 3,
    'operation': 'add'
  },
  outputValues: {
    'result': 8
  },
  internalState: {
    'history': [5, 8, 13]
  }
}
```

---

## 🏟📍⌛🧈➕🟢 State Management District

### 🏟⌛📍🟢 - Variable Scopes.parti

| Scope | Visibility | Lifetime | Access |
|-------|------------|----------|--------|
| global | Entire .parti file | Session | Any block |
| block | Within single block | Block exists | Block + children |
| local | Within execution | Execution | Current context |
| zip | All blocks at same zip | Session | Zip-matched blocks |

```typescript
interface VariableScopes {
  global: Map<string, any>    // Entire file
  block: Map<string, any>     // Per block
  local: Map<string, any>     // Per execution
  zip: Map<ZipCode, Map<string, any>>  // Per zip
}
```

---

### 🏟⌛📍🟢 - Block States.parti

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Created ──▶ Idle ◀────▶ Executing ──▶ Complete            │
│                 │            │            │                 │
│                 ▼            ▼            ▼                 │
│              Locked       Error      Paused                 │
│                 │            │            │                 │
│                 ▼            ▼            ▼                 │
│              Hidden      Deleted (in 🧮 undo stack)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

```typescript
type BlockState = 
  | 'created'     // Just spawned
  | 'idle'        // Waiting
  | 'executing'   // Running code/triggers
  | 'complete'    // Finished successfully
  | 'error'       // Something went wrong
  | 'paused'      // Suspended
  | 'locked'      // Protected from edits (can still execute)
  | 'hidden'      // Invisible but exists
  | 'deleted'     // In undo stack
```

**State Transitions:**
| From | To | Trigger |
|------|-----|---------|
| created | idle | init complete |
| idle | executing | trigger fired |
| executing | complete | success |
| executing | error | failure |
| any | locked | user lock |
| any | hidden | user hide |
| any | deleted | user delete |

---

## 🏟📍🫀🧈➕🔵 Execution Patterns District

### 🏟🫀📍🔵 - Common Patterns.parti

**Counter Pattern:**
```scl
🐂📍 count 0
🦉 buttonTapped ↳
  ➕ count 1
  🚀🛒 count
```

**Form Submission Pattern:**
```scl
🐂📍 formData {}
🧲🪡 name "Name:"
🧲🪡 email "Email:"
🦉 submitClicked ↳
  📍 formData {name, email}
  🚀🛒🎯 backend formData
```

**Navigation Pattern:**
```scl
🦉 menuItemTapped ↳
  🦉 item === "home" ↳
    🧸 🏠
  🦉 item === "settings" ↳
    🧸 🎯⚙️
```

**Timer Pattern:**
```scl
🐂📍 elapsed 0
⌛🦋 1000 ↳
  ➕ elapsed 1
  🚀🛒 elapsed
```

---

## Cross-References

| This Order | References | Relationship |
|------------|------------|--------------|
| 🏟 Execution | 🐂 Foundation | Executes foundation structures |
| 🏟 Execution | ⛽ Validation | Enforces constraints during execution |
| 🏟 Execution | 🌾 Integration | Connects systems at runtime |

---

## District Summary

| District | Zip | Items | Status |
|----------|-----|-------|--------|
| SCL Interpreter | 🏟📍🦉🧈➕🔵 | 2 | ✅ Complete |
| Python Bridge | 🏟📍🐍🧈➕🔵 | 3 | ✅ Complete |
| Trigger Execution | 🏟📍🤌🧈➕🔵 | 3 | ✅ Complete |
| Navigation | 🏟📍🧸🧈➕🔵 | 3 | ✅ Complete |
| Tool Execution | 🏟📍🚀🧈➕🔵 | 2 | ✅ Complete |
| State Management | 🏟📍⌛🧈➕🟢 | 2 | ✅ Complete |
| Execution Patterns | 🏟📍🫀🧈➕🔵 | 1 | ✅ Complete |

**Total: 16 items across 7 districts**

---

*🏟 Corinthian — Where the ornate work of execution happens.*
