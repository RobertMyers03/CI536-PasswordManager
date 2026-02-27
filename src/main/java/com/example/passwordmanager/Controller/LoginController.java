package com.example.passwordmanager.Controller;

import com.example.passwordmanager.PasswordManagerApplication;
import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Node;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.PasswordField;
import javafx.scene.control.TextField;
import javafx.stage.Stage;

import java.io.IOException;

public class LoginController {

    @FXML Button loginButton;
    @FXML TextField usernameField;
    @FXML PasswordField passwordField;
    @FXML Label errorLabel;

    SceneController sceneController = new SceneController();

    public LoginController(){
    }

    @FXML
    public void HandleLoginButton(ActionEvent event) throws IOException{ // temporary login details
        String username = usernameField.getText();
        String password = passwordField.getText();

        if(username.equals("admin") && password.equals("admin")){
            sceneController.SwitchToDashboard(event);
        }else{
            errorLabel.setVisible(true);
            errorLabel.setText("Login Failed");
        }
    }

}

