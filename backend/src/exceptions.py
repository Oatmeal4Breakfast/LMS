from uuid import UUID


# User Domain Errors
class InvalidNameError(Exception):
    def __init__(self, length: int) -> None:
        self.length: int = length
        super().__init__(f"Name must be between 1 and {length}")


class UserNotFoundError(Exception):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"User not found: {identifier}")


class UserAlreadyExistsError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"User with email '{email}' already exists")


class UserCannotBeDeletedError(Exception):
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        super().__init__(f"User with id {user_id} cannot be deleted")


class UserCannotBeUpdatedError(Exception):
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        super().__init__(f"User with id {user_id} cannot be updated")


class UserAlreadyAssignedError(Exception):
    def __init__(self, user_id: UUID, training_path_id: UUID) -> None:
        self.user_id = user_id
        self.training_path_id = training_path_id
        super().__init__(
            f"User {user_id} is already assigned to training path {training_path_id}"
        )


class UserNotAssignedError(Exception):
    def __init__(self, user_id: UUID, training_path_id: UUID) -> None:
        self.user_id = user_id
        self.training_path_id = training_path_id
        super().__init__(
            f"User {user_id} is not assigned to training path {training_path_id}"
        )


# Training Path Domain Errors
class TrainingPathNotFoundError(Exception):
    def __init__(self, training_path_id: UUID) -> None:
        self.training_path_id = training_path_id
        super().__init__(f"TrainingPath with id {training_path_id} not found")


class TrainingPathAlreadyExistsError(Exception):
    def __init__(self, title: str) -> None:
        self.title = title
        super().__init__(f"TrainingPath with title '{title}' already exists")


class TrainingPathCannotBeDeletedError(Exception):
    def __init__(self, training_path_id: UUID) -> None:
        self.training_path_id = training_path_id
        super().__init__(f"TrainingPath with id {training_path_id} cannot be deleted")


class TrainingPathAlreadyAssignedError(Exception):
    def __init__(self, tp_id: UUID, user_id: UUID) -> None:
        self.tp_id = tp_id
        self.user_id = user_id
        super().__init__(f"TrainingPath {tp_id} is already assigned to user {user_id}")


class TrainingPathNotAssignedError(Exception):
    def __init__(self, tp_id: UUID, user_id: UUID) -> None:
        self.tp_id = tp_id
        self.user_id = user_id
        super().__init__(f"TrainingPath {tp_id} is not assigned to user {user_id}")


class TrainingPathCannotBeUpdatedError(Exception):
    def __init__(self, training_path_id: UUID) -> None:
        self.training_path_id = training_path_id
        super().__init__(f"TrainingPath with id {training_path_id} cannot be updated")


class InvalidTrainingPathError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# Lesson Domain Errors
class LessonNotFoundError(Exception):
    def __init__(self, lesson_id: UUID) -> None:
        self.lesson_id = lesson_id
        super().__init__(f"Lesson with id {lesson_id} not found")


class LessonAlreadyExistsError(Exception):
    def __init__(self, title: str) -> None:
        self.title = title
        super().__init__(f"Lesson with title '{title}' already exists")


class LessonNotExistsError(Exception):
    def __init__(self, lesson_id: UUID) -> None:
        self.lesson_id = lesson_id
        super().__init__(f"Lesson with id {lesson_id} does not exist")


class LessonNotAssignedError(Exception):
    def __init__(self, lesson_id: UUID, training_path_id: UUID) -> None:
        self.lesson_id = lesson_id
        self.training_path_id = training_path_id
        super().__init__(
            f"Lesson {lesson_id} is not assigned to training path {training_path_id}"
        )


class LessonAlreadyAssignedError(Exception):
    def __init__(self, lesson_id: UUID, training_path_id: UUID) -> None:
        self.lesson_id = lesson_id
        self.training_path_id = training_path_id
        super().__init__(
            f"Lesson {lesson_id} is already assigned to training path {training_path_id}"
        )


class LessonCannotBeDeletedError(Exception):
    def __init__(self, lesson_id: UUID) -> None:
        self.lesson_id = lesson_id
        super().__init__(f"Lesson with id {lesson_id} cannot be deleted")


class LessonCannotBeUpdatedError(Exception):
    def __init__(self, lesson_id: UUID) -> None:
        self.lesson_id = lesson_id
        super().__init__(f"Lesson with id {lesson_id} cannot be updated")


class InvalidLessonError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# Quiz Domain Errors
class QuizNotFoundError(Exception):
    def __init__(self, identifier: UUID | str) -> None:
        self.identifier = identifier
        super().__init__(f"Quiz with id {identifier} not found")


class QuizAlreadyExistsError(Exception):
    def __init__(self, title: str) -> None:
        self.title = title
        super().__init__(f"Quiz with title '{title}' already exists")


class QuizCannotBeDeletedError(Exception):
    def __init__(self, quiz_id: UUID) -> None:
        self.quiz_id = quiz_id
        super().__init__(f"Quiz with id {quiz_id} cannot be deleted")


class QuizCannotBeUpdatedError(Exception):
    def __init__(self, quiz_id: UUID) -> None:
        self.quiz_id = quiz_id
        super().__init__(f"Quiz with id {quiz_id} cannot be updated")


class QuizNotAssignedError(Exception):
    def __init__(self, quiz_id: UUID, lesson_id: UUID) -> None:
        self.quiz_id = quiz_id
        self.lesson_id = lesson_id
        super().__init__(f"Quiz {quiz_id} is not assigned to lesson {lesson_id}")


class QuizAlreadyAssignedError(Exception):
    def __init__(self, quiz_id: UUID, lesson_id: UUID) -> None:
        self.quiz_id = quiz_id
        self.lesson_id = lesson_id
        super().__init__(f"Quiz {quiz_id} is already assigned to lesson {lesson_id}")


class InvalidQuizError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# Question Domain Errors
class InvalidQuestionError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidAnswerError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class QuestionAnswerNotFoundError(Exception):
    def __init__(self, answer: str) -> None:
        self.answer = answer
        super().__init__(f"Answer '{answer}' does not exist as a possible answer")


class AnswerAlreadyExistsError(Exception):
    def __init__(self, answer: str) -> None:
        self.answer = answer
        super().__init__(f"Answer '{answer}' already exists as a possible answer")


class QuestionNotAssignedError(Exception):
    def __init__(self, question_id: UUID, quiz_id: UUID) -> None:
        self.question_id = question_id
        self.quiz_id = quiz_id
        super().__init__(f"Question {question_id} is not assigned to quiz {quiz_id}")


class QuestionAlreadyAssignedError(Exception):
    def __init__(self, question_id: UUID, quiz_id: UUID) -> None:
        self.question_id = question_id
        self.quiz_id = quiz_id
        super().__init__(
            f"Question {question_id} is already assigned to quiz {quiz_id}"
        )


class QuestionNotFoundError(Exception):
    def __init__(self, question_id: UUID) -> None:
        self.question_id = question_id
        super().__init__(f"Question with id {question_id} not found")


class QuestionCannotBeUpdatedError(Exception):
    def __init__(self, question_id: UUID) -> None:
        self.question_id = question_id
        super().__init__(f"Question with id {question_id} cannot be updated")


class QuestionCannotBeDeletedError(Exception):
    def __init__(self, question_id: UUID) -> None:
        self.question_id = question_id
        super().__init__(f"Question with id {question_id} cannot be deleted")


class QuestionAlreadyExistsError(Exception):
    def __init__(self, question_id: UUID) -> None:
        self.question_id = question_id
        super().__init__(f"Question with id {question_id} already exists")


# General DB Errors
class DatabaseConflictError(Exception):
    pass


class DatabaseUnavailableError(Exception):
    pass


# Auth Domain Errors
class InvalidCredentialsError(Exception):
    pass


class AuthenticationError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Unable to authenticate user {email}")


class InvalidTokenError(Exception):
    pass


class ServiceUnavailableError(Exception):
    pass


class InvalidEmailError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"'{email}' is not a valid email address")
