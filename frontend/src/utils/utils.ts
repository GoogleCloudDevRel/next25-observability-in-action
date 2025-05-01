var constants = {
    backendURL: "https://quiz-483420602709.us-central1.run.app",
    demoTitle: "Observability in Action",
    demoSubtitle: "Learn with logs",
    numQuestions: 3
}

var prompt = ""
var sessionId = ""

var questions: any[] = []
var currQuestion = 0

function getPrompt() {
    return prompt
}

function setPrompt(text: string) {
    console.log("POST /prompt " + text)

    prompt = text
    sessionId = String(Date.now())
    console.log("Set sessionID to " + sessionId)
    console.log("Set prompt to " + prompt)

    fetch(constants.backendURL + "/prompt?" + new URLSearchParams({
        prompt: prompt,
        sid: sessionId
    }), {
        method: "POST"
    })
    .then(response => response.json())
    .then(data => {
        questions = data["player_questions"]
        console.log(questions)
        currQuestion = 0

        return
    })
}

function getQuestion() {
    var q = questions[currQuestion]
    currQuestion += 1

    console.log("getting question...")
    console.log(q)
    return q
}

function getAllQuestions() {
    return questions
}

function postResponse(qid: string, answer: string) {
    console.log("POST /answer " + qid + " " + answer)
    for (let i in questions) {
        if (questions[i].qid == qid) {
            questions[i].tried_code = answer
        }
    }
    
    fetch(constants.backendURL + "/answer?" + new URLSearchParams({
        answer: answer,
        qid: qid,
        sid: sessionId
    }), {
        method: "POST"
    })
    .then(response => response.json())
    .then(data => {
        console.log(data)
        
        return
    })
}

function finalize() {
    console.log("GET /final")

    fetch(constants.backendURL + "/final?" + new URLSearchParams({
        sid: sessionId
    }))
    .then(response => response.json())
    .then(data => {
        console.log(data)
        return
    })
}

export { constants, getPrompt, setPrompt, getQuestion, postResponse, getAllQuestions, finalize }
