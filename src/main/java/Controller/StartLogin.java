package Controller;

import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextField;

public class StartLogin {

    @FXML
    Button loginButton;
    @FXML
    TextField usernameField;
    @FXML
    TextField passwordField;
    @FXML
    Label errorLabel;

    public StartLogin(){
    }

    @FXML
    public void HandleLoginButton()
    {
        String username = usernameField.getText();
        String password = passwordField.getText();

        // temporary credentials to test login
        if(username.equals("admin") && password.equals("admin")){
            System.out.println("Login Successful");
            errorLabel.setVisible(false);
        }else{
            errorLabel.setVisible(true);
            errorLabel.setText("Login Failed");
        }

        // change scene
    }
}
