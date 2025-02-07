from abc import abstractmethod, ABC
from typing import Any, List

from ..constants import PromptOptimizationParams


class PromptOptimizer(ABC):
    """
    Parent class for all prompt optimization techniques.
    """
    TECHNIQUE_NAME = ""

    @abstractmethod
    def get_best_prompt(self, params: PromptOptimizationParams) -> (str, Any):
        """Method that will return best prompt for given task description, base instruction and few shot examples"""
        pass


class DatasetSpecificProcessing(ABC):
    """
    Prompt Optimizer is agnostic of dataset on which its run. There are few processing requirements that are specific
    to dataset. This class should be inherited class that user defines & its methods should be defined based on their
    dataset & use-case.
    """
    QUESTION_LITERAL = "question"
    ANSWER_WITH_REASON_LITERAL = "answer"
    FINAL_ANSWER_LITERAL = "answer"
    QUESTION_KEY_IN_PROMPT = "[Question]"
    ANSWER_KEY_IN_PROMPT = "[Answer]"
    # Regular expression pattern to match text between <START> and <END> tags
    TEXT_DELIMITER_PATTERN = r"(?s)(?<=<START>)(.*?)(?=<END>)"
    TEXT_DELIMITER_PATTERN_MUTATION = r"(?s)(?<=<START>)(.*?)(?=<END>)"
    ANSWER_START = "<ANS_START>"
    ANSWER_END = "<ANS_END>"
    ANSWER_DELIMITER_PATTERN = r"(?s)(?<=" + ANSWER_START + ")(.*?)(?=" + ANSWER_END + ")"
    INVALID_ANS = "[invalid]"
    FINAL_PROMPT = None
    
    
    def normalize_prediction(self, prediction, lowercase=True):
        import re
        import string
        prediction = prediction.replace(' and ', ' ')
        prediction = prediction.replace('Sentence 1:', ' ')
        prediction = prediction.replace('Sentence 2:', ' ')
        prediction = prediction.strip()
        prediction = prediction.split("\n")[0]
        prediction = prediction.split(".")[0]

        if lowercase:
            prediction = prediction.lower()

        # remove punctuation
        prediction = prediction.replace('-', ' ')
        prediction = prediction.translate(
            str.maketrans('', '', string.punctuation))

        return prediction
    def access_answer(self, llm_output: str, gt_answer: str) -> (bool, Any):
        """
        Compare answer generated by model with the answer in ground truth.
        Return True if they are equal. Definition of `equal` depends on problem at hand.
        Here only the default implementation is provided. This method should be overridden & custom defined
        based on end use-case.

        :param llm_output: Output of LLM i.e. the predicted answer
        :param gt_answer: The expected ground truth answer
        """

        predicted_answer = self.extract_final_answer(llm_output)
        is_correct = False
        if predicted_answer and (predicted_answer.lower() == gt_answer.lower()):
            is_correct = True

        return is_correct, predicted_answer
   
    

    def collate_to_str(self, examples: List, example_template: str) -> str:
        """
        Take as input a list of examples. Populate common template with values in these examples. Concatenate all of
        them to a single string, which can then be passed to LLM as prompt.

        :param examples: List of examples
        :param example_template: A template of giving examples to LLM as part of few shot learning
        :return: Concatenated string of all examples over the template.
        """
        example_string = ""
        for example in examples:
            answer = example[DatasetSpecificProcessing.FINAL_ANSWER_LITERAL]
            if DatasetSpecificProcessing.ANSWER_WITH_REASON_LITERAL in example:
                answer = example[DatasetSpecificProcessing.ANSWER_WITH_REASON_LITERAL]

            example_string += example_template.format(question=example[DatasetSpecificProcessing.QUESTION_LITERAL],
                                                      answer=answer)
        return example_string

    def extract_final_answer(self, answer: str) -> str:
        """
        Parse the output of LLM and extract the answer that you need from it.
        Here only the default implementation is provided. This method should be overridden & custom defined
        based on end use-case.

        :param answer: Output of LLM i.e. the response the to the question asked.
        :return: Final answer extracted from `answer` text, that we are looking for.
        """
        
        return answer

    @abstractmethod
    def dataset_to_jsonl(self, dataset_jsonl: str, task: str, **kwargs: Any) -> None:
        """
        Prompt optimizer needs data in jsonl format. And each json string should be as below
        {
          'question': 'I had 3 books. I gave 2 books to Ram. How many books do I have now ?',
          'reason': 'Number of books that I had initially=1. Number of books I have after giving 2 books to Ram=3-2=1.',
          'answer': 1)
        }

        :param dataset_jsonl: Path of file in which jsonl data should be saved.
        :param **kwargs: List of other user defined input parameters.
        """
        pass
