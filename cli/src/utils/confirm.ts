import prompts from 'prompts';

export async function confirm(text: string, defaultAnswer = false) {
  const response = await prompts({
    type: 'confirm',
    name: 'value',
    message: text,
    initial: defaultAnswer,
  });
  return response.value;
}

/*
export async function confirm(text: string, defaultAnwser = false) {
  const inquirer = await import('inquirer')
  const confirmAnswers = await inquirer.default.prompt([
    {
      name: 'confirm',
      type: 'confirm',
      default: defaultAnwser,
      message: text,
    },
  ])

  return confirmAnswers['confirm'] as boolean
}*/
