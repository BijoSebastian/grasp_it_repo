# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 10:33:31 2024

@author: aslwo
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
#import torchvision.models.vision_transformer.VisionTransformer as VisionTransformer
#from transformers import VisionTransformer, SwinTransformer
import timm

class CNN_Position_Orientation(nn.Module):
    def __init__(self, num_outputs=1):
        super(CNN_Position_Orientation, self).__init__()
        self.num_outputs = num_outputs

        # Define convolutional layers for image processing
        self.conv1 = nn.Conv2d(in_channels=4, out_channels=16, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1)
        self.conv4 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1)
        self.conv5 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=1, padding=1)
        
        # Define fully connected layers for position prediction
        self._to_fc_input_size = self._calculate_conv_output_size()
        #print('shape',self._to_fc_input_size)

        # Define fully connected layers for position prediction
        self.fc_position1 = nn.Linear(self._to_fc_input_size, 1024)
        #self.fc_position1 = nn.Linear(64 * 64 * 64, 1024)
        self.fc_position2 = nn.Linear(1024, 3 * num_outputs)  # Output 5 sets of 3D positions

        # Define fully connected layers for orientation prediction
        self.fc_orientation1 = nn.Linear(self._to_fc_input_size, 1024)
        self.fc_orientation2 = nn.Linear(1024, 4 * num_outputs)  # Output 10 sets of quaternions

    def forward(self, x):
        # Forward pass through convolutional layers
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, kernel_size=2, stride=2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, kernel_size=2, stride=2)
        x = F.relu(self.conv3(x))
        x = F.max_pool2d(x, kernel_size=2, stride=2)
        x = F.relu(self.conv4(x))
        x = F.max_pool2d(x, kernel_size=2, stride=2)
        x = F.relu(self.conv5(x))
        x = F.max_pool2d(x, kernel_size=2, stride=2)

        # Flatten the output for fully connected layers
        x = x.view(x.size(0), -1)
        #print('forward',x.shape)
        # Position prediction
        position = F.relu(self.fc_position1(x))
        position = self.fc_position2(position)
        position = position.view(-1, self.num_outputs, 3)  # Reshape to (batch_size, num_outputs, 3)

        # Orientation prediction
        orientation = F.relu(self.fc_orientation1(x))
        orientation = self.fc_orientation2(orientation)
        orientation = orientation.view(-1, self.num_outputs, 4)  # Reshape to (batch_size, num_outputs, 4)
        #orientation = F.softmax(orientation, dim=-1)
        orientation_norm = torch.norm(orientation, dim=-1, keepdim=True)
        orientation = orientation / orientation_norm

        return position, orientation
    
    def _calculate_conv_output_size(self):
        # Define a method to calculate the output size of convolutional layers
        # to determine the input size for the fully connected layer
        with torch.no_grad():
            dummy_input = torch.zeros(32, 4, 512, 512) 
            x = F.relu(self.conv1(dummy_input))
            x = F.max_pool2d(x, kernel_size=2, stride=2)
            x = F.relu(self.conv2(x))
            x = F.max_pool2d(x, kernel_size=2, stride=2)
            x = F.relu(self.conv3(x))
            x = F.max_pool2d(x, kernel_size=2, stride=2)
            x = F.relu(self.conv4(x))
            x = F.max_pool2d(x, kernel_size=2, stride=2)
            x = F.relu(self.conv5(x))
            x = F.max_pool2d(x, kernel_size=2, stride=2)
            #conv_output_size = x.view(1, -1).size(1)
            conv_output_size = x.view(x.size(0), -1).size(1)
        return conv_output_size


class MyModel(nn.Module):
    def __init__(self, num_filter=[16,16,16,16,16], kernel_size=[5, 5, 5, 5, 5], stride=[1, 1, 1, 1, 1], padding=[1, 1, 1, 1, 1], activation='relu',batch_normalization='False',dropout=0.2):
        super(MyModel, self).__init__()
        self.num_filter = num_filter
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.activation = activation
        self.batch_normalization=batch_normalization

        self.conv1 = nn.Conv2d(4, num_filter[0], kernel_size=kernel_size[0], stride=stride[0], padding=padding[0])
        self.bn1 = nn.BatchNorm2d(num_filter[0])
        self.dropout1 = nn.Dropout(dropout)
        self.conv2 = nn.Conv2d(num_filter[0], num_filter[1], kernel_size=kernel_size[1], stride=stride[1], padding=padding[1])
        self.bn2 = nn.BatchNorm2d(num_filter[1])
        self.dropout2 = nn.Dropout(dropout)
        self.conv3 = nn.Conv2d(num_filter[1], num_filter[2], kernel_size=kernel_size[2], stride=stride[2], padding=padding[2])
        self.bn3 = nn.BatchNorm2d(num_filter[2])
        self.dropout3 = nn.Dropout(dropout)
        self.conv4 = nn.Conv2d(num_filter[2], num_filter[3], kernel_size=kernel_size[3], stride=stride[3], padding=padding[3])
        self.bn4 = nn.BatchNorm2d(num_filter[3])
        self.dropout4 = nn.Dropout(dropout)
        self.conv5 = nn.Conv2d(num_filter[3], num_filter[4], kernel_size=kernel_size[4], stride=stride[4], padding=padding[4])
        self.bn5 = nn.BatchNorm2d(num_filter[4])
        self.dropout5 = nn.Dropout(dropout)

        if activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'gelu':
            self.activation = nn.GELU()
        elif activation == 'elu':
            self.activation = nn.ELU()
        elif activation == 'silu':
            self.activation = nn.SiLU()
        
        self.pooling = nn.MaxPool2d(kernel_size=2)

        self.avgpool=nn.AdaptiveAvgPool2d(output_size=(1, 1))
        self.dense=nn.Linear(num_filter[4],256)
        self.fc = nn.Linear(256, 10)

    def forward(self, x):
        x = self.conv1(x)
        if self.batch_normalization: x = self.bn1(x)         
        x = self.activation(x)
        x=self.dropout1(x)
        x = self.pooling(x)
      
        x = self.conv2(x)
        if self.batch_normalization: x = self.bn2(x)
        x = self.activation(x)
        x=self.dropout2(x)
        x = self.pooling(x)

        x = self.conv3(x)
        if self.batch_normalization: x = self.bn3(x)
        x = self.activation(x)
        x=self.dropout3(x)
        x = self.pooling(x)

        x = self.conv4(x)
        if self.batch_normalization: x = self.bn4(x)
        x = self.activation(x)
        x=self.dropout4(x)
        x = self.pooling(x)

        x = self.conv5(x)
        if self.batch_normalization: x = self.bn5(x)
        x = self.activation(x)
        x=self.dropout5(x)
        x = self.pooling(x)

        x = self.avgpool(x)#read why cant we use maxpooling here
        x = torch.flatten(x, 1)
        x = self.dense(x)
        x = self.fc(x)

        return x


class ResNet_Position_Orientation(nn.Module):
    def __init__(self, num_outputs=1, freeze_weights = True):
        super(ResNet_Position_Orientation, self).__init__()
        self.num_outputs = num_outputs

        # Load pretrained ResNet50 model
        pretrained_resnet = models.resnet50(pretrained = freeze_weights)
        # Modify the first convolutional layer to accept 4 input channels
        pretrained_resnet.conv1 = nn.Conv2d(4, 64, kernel_size=7, stride=2, padding=3, bias=False)

        # Remove the classification layer (fully connected layer) at the end
        self.resnet_features = nn.Sequential(*list(pretrained_resnet.children())[:-1])

        # Define fully connected layers for position prediction
        self.fc_position1 = nn.Linear(2048, 1024)
        self.fc_position2 = nn.Linear(1024, 3 * num_outputs)  # Output 1 sets of 3D positions

        # Define fully connected layers for orientation prediction
        self.fc_orientation1 = nn.Linear(2048, 4096)
        self.fc_orientation2 = nn.Linear(4096, 2048)
        self.fc_orientation3 = nn.Linear(2048, 4 * num_outputs)  # Output 1 sets of quaternions

    def forward(self, x):
        # Forward pass through ResNet features
        features = self.resnet_features(x)
        features = features.view(features.size(0), -1)

        # Position prediction
        position = F.relu(self.fc_position1(features))
        position = self.fc_position2(position)
        position = position.view(-1, self.num_outputs, 3)  # Reshape to (batch_size, num_outputs, 3)

        # Orientation prediction
        orientation = F.relu(self.fc_orientation1(features))
        orientation = self.fc_orientation2(orientation)
        orientation = self.fc_orientation3(orientation)
        orientation = orientation.view(-1, self.num_outputs, 4)  # Reshape to (batch_size, num_outputs, 4)
        orientation_norm = torch.norm(orientation, dim=-1, keepdim=True)
        orientation = orientation / orientation_norm

        return position, orientation
    

'''
class Vision_Transformer_Position_Orientation(nn.Module):
    def __init__(self, num_outputs=1):
        super(Vision_Transformer_Position_Orientation, self).__init__()
        self.num_outputs = num_outputs

        # Load pretrained Vision Transformer model
        pretrained_vit = VisionTransformer.from_pretrained('google/vit-base-patch16-224-in21k')
        # Modify input layer to accept 4 input channels
        pretrained_vit.patch_embed.proj = nn.Conv2d(4, 768, kernel_size=16, stride=16)

        self.vit_features = pretrained_vit

        # Define fully connected layers for orientation prediction
        self.fc_orientation1 = nn.Linear(768, 2048)
        self.fc_orientation2 = nn.Linear(2048, 1024)
        self.fc_orientation3 = nn.Linear(1024, 4 * num_outputs)  # Output 10 sets of quaternions

    def forward(self, x):
        # Forward pass through Vision Transformer features
        features = self.vit_features(x)
        features = features[:, 0]  # Only take the first token (CLS token)

        # Orientation prediction
        orientation = F.relu(self.fc_orientation1(features))
        orientation = F.relu(self.fc_orientation2(orientation))
        orientation = self.fc_orientation3(orientation)
        orientation = orientation.view(-1, self.num_outputs, 4)  # Reshape to (batch_size, num_outputs, 4)
        orientation_norm = torch.norm(orientation, dim=-1, keepdim=True)
        orientation = orientation / orientation_norm

        return orientation

class Swin_Transformer_Position_Orientation(nn.Module):
    def __init__(self, num_outputs=1):
        super(Swin_Transformer_Position_Orientation, self).__init__()
        self.num_outputs = num_outputs

        # Load pretrained Swin Transformer model
        pretrained_swin = SwinTransformer(img_size=224, patch_size=4, in_chans=4)
        self.swin_features = pretrained_swin

        # Define fully connected layers for orientation prediction
        self.fc_orientation1 = nn.Linear(1024, 2048)
        self.fc_orientation2 = nn.Linear(2048, 4 * num_outputs)  # Output 10 sets of quaternions

    def forward(self, x):
        # Forward pass through Swin Transformer features
        features = self.swin_features(x)

        # Orientation prediction
        orientation = F.relu(self.fc_orientation1(features))
        orientation = self.fc_orientation2(orientation)
        orientation = orientation.view(-1, self.num_outputs, 4)  # Reshape to (batch_size, num_outputs, 4)
        orientation_norm = torch.norm(orientation, dim=-1, keepdim=True)
        orientation = orientation / orientation_norm

        return orientation
'''
class ConvNet_Position_Orientation(nn.Module):
    def __init__(self, num_outputs=1):
        super(ConvNet_Position_Orientation, self).__init__()
        self.num_outputs = num_outputs

        # Define ConvNet architecture
        self.conv1 = nn.Conv2d(4, 32, kernel_size=3)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3)
        self.conv5 = nn.Conv2d(256, 512, kernel_size=3)
        self.conv6 = nn.Conv2d(512, 1024, kernel_size=3)
        self.fc_orientation = nn.Linear(1024, 4 * num_outputs)  # Output 10 sets of quaternions

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = F.relu(self.conv4(x))
        x = F.relu(self.conv5(x))
        x = F.relu(self.conv6(x))
        x = F.adaptive_avg_pool2d(x, (1, 1))
        x = x.view(-1, 1024)
        orientation = self.fc_orientation(x)
        orientation = orientation.view(-1, self.num_outputs, 4)  # Reshape to (batch_size, num_outputs, 4)
        orientation_norm = torch.norm(orientation, dim=-1, keepdim=True)
        orientation = orientation / orientation_norm

        return orientation

class VGG_Position_Orientation(nn.Module):
    def __init__(self, num_outputs=1):
        super(VGG_Position_Orientation, self).__init__()
        self.num_outputs = num_outputs

        # Load pretrained VGG model
        pretrained_vgg = models.vgg16(pretrained=True)
        self.features = pretrained_vgg.features

        # Define fully connected layers for orientation prediction
        self.fc_orientation1 = nn.Linear(512 * 7 * 7, 4096)
        self.fc_orientation2 = nn.Linear(4096, 4096)
        self.fc_orientation3 = nn.Linear(4096, 4 * num_outputs)  # Output 10 sets of quaternions

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc_orientation1(x))
        x = F.relu(self.fc_orientation2(x))
        orientation = self.fc_orientation3(x)
        orientation = orientation.view(-1, self.num_outputs, 4)  # Reshape to (batch_size, num_outputs, 4)
        orientation_norm = torch.norm(orientation, dim=-1, keepdim=True)
        orientation = orientation / orientation_norm

        return orientation

class EfficientNet_Position_Orientation(nn.Module):
    def __init__(self, num_outputs=1, freeze_weights = True):
        super(EfficientNet_Position_Orientation, self).__init__()
        self.num_outputs = num_outputs

        # Load pretrained EfficientNet model
        pretrained_effnet = timm.create_model('efficientnet_b0', pretrained=freeze_weights)
        if hasattr(pretrained_effnet, 'conv_stem'):
            pretrained_effnet.conv_stem = nn.Conv2d(4, 32, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
       
        self.features = pretrained_effnet

        # Remove the classification layer (fully connected layer) at the end
        self.effnet_features = nn.Sequential(*list(pretrained_effnet.children())[:-1])


        # Define fully connected layers for orientation prediction
        #self.fc_orientation1 = nn.Linear(1280, 512)
        #self.fc_orientation2 = nn.Linear(512, 4 * num_outputs)  # Output 10 sets of quaternions
        
        self.fc_position1 = nn.Linear(1280, 1024)
        self.fc_position2 = nn.Linear(1024, 3 * num_outputs)  # Output 10 sets of quaternions

    def forward(self, x):
        features = self.effnet_features(x)
        features = features.view(features.size(0), -1)

        # Position prediction
        position = F.relu(self.fc_position1(features))
        position = self.fc_position2(position)
        position = position.view(-1, self.num_outputs, 3)  # Reshape to (batch_size, num_outputs, 3)

        return position
    