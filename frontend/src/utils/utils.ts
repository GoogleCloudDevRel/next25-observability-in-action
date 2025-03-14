var constants = {
    demoTitle: "Observability in Action",
    demoSubtitle: "Learn with logs",
    numQuestions: 3
}

var prompt = ""

var mockQuestionCounter = 0
var mockQuestions = [
    {
        id: 0,
        question: "What is 1+1?",
        options: [
            "2",
            "3",
            "4"
        ],
        answer: "2"
    },
    {
        id: 2,
        question: "What is 2+2?",
        options: [
            "4",
            "5",
            "6"
        ],
        answer: "4"
    },
    {
        id: 3,
        question: "What is 3+3?",
        options: [
            "6",
            "7",
            "8"
        ],
        answer: "6"
    }
]

function getPrompt() {
    return prompt
}

function setPrompt(text: string) {
    prompt = text
}

function getQuestion() {
    // @TODO: call GET /question
    mockQuestionCounter++
    return mockQuestions[mockQuestionCounter % 3]
}

function postResponse(id: number, response: string) {
    // @TODO: call POST /question/id
    console.log(id, response)
}

function callModel(model: string):string {
    // @TODO: call POST /llm
    return "This is what the model returned!"
}

export { constants, getPrompt, setPrompt, getQuestion, postResponse, callModel }
