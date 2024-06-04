package cadastrodeoperador

import (
	"fmt"
)

func Cadastro() {
	var (
		cod         uint8
		nome        string
		senha       string
		validaSenha string
		tipo        string
	)
	fmt.Println("CADASTRO DE OPERADOR")

	fmt.Printf("Codigo:")
	fmt.Scanln(&cod)

	fmt.Printf("Nome:")
	fmt.Scanln(&nome)

	tipo = validaTipo()

	fmt.Printf("Senha:")
	fmt.Scanln(&senha)

	fmt.Printf("Repita a senha:")
	fmt.Scanln(&validaSenha)

	if senha != validaSenha {
		fmt.Println("Senhas Não batem")
		Cadastro()
	}

	fmt.Println(cod, nome, senha, tipo)
}

func validaTipo() string {
	tp := 0
	tipo := ""
	if tp == 0 {
		fmt.Printf("tipo [ 1 ] Supervisor [ 2 ] Operador:")
		fmt.Scanln(&tp)
		if tp == 1 {
			tipo = "Supervisor"
		} else if tp == 2 {
			tipo = "Operador"
		} else {
			validaTipo()
		}
	}
	return tipo
}
