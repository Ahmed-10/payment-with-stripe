
let features = []
const checkboxes = Array.from(document.getElementsByClassName('checkbox'));
checkboxes.forEach((checkbox) => {
    checkbox.addEventListener('click', (event)=>{
        if(checkbox.checked === true){
            features.push(featuresList[event.target.value - 1])
        } else {
            const i = features.indexOf(featuresList[event.target.value - 1])
            features.splice(i, 1)
        }
    })
})

const planName = document.getElementById('plan-name')
const price = document.getElementById('price')


document.getElementById('submit').addEventListener('click', async(event) => {
    event.preventDefault();
    features.sort();
    for(let i in features){
        features[i] = features[i].split('.')[1]
    }
    fetch('/plans',{
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            plan_name: planName.value,
            price: price.value,
            features: features
        })
    }).then((res)=> res.json())
    .then((res) => {
        if(res.message === 'success'){
            window.location.href = `${ window.origin }/plans/${ res.plan.id}`
        }
    })
})